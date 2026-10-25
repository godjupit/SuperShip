"""Check sampling boundaries, strided values and CUDA Graph reuse against PyTorch."""
import pytest
import torch
from engine.rtv4.utils import deformable_attention_core_func_v2


@pytest.mark.skipif(not torch.cuda.is_available(), reason='CUDA required')
@pytest.mark.parametrize('dtype', [torch.float16, torch.float32])
def test_fused_attention_matches_bilinear_reference_and_reuses_graph(monkeypatch, dtype):
    torch.manual_seed(21)
    shapes = [(7, 9), (3, 4), (1, 2)]
    points = [2, 3, 1]
    n, q, heads, c = 2, 11, 2, 5
    # Same noncontiguous token-major views as the real decoder, including level offsets.
    memory = torch.randn(n, sum(h*w for h,w in shapes), heads*c, device='cuda', dtype=dtype)
    values = memory.reshape(n, -1, heads, c).permute(0, 2, 3, 1).split([h*w for h,w in shapes], dim=-1)
    locations = torch.rand(n, q, heads, sum(points), 2, device='cuda') * 1.6 - .3
    locations[:, :2] = torch.tensor([0., 1.], device='cuda').view(1, 2, 1, 1, 1)
    weights = torch.randn(n, q, heads, sum(points), device='cuda', dtype=dtype).softmax(-1)
    def run(impl):
        monkeypatch.setenv('DEFORM_ATTN_IMPL', impl)
        with torch.inference_mode(), torch.autocast('cuda', dtype=torch.float16):
            return deformable_attention_core_func_v2(values, shapes, locations, weights, points)
    expected = run('torch')
    actual = run('triton')
    torch.testing.assert_close(actual, expected, rtol=1e-4, atol=1e-5)
    assert actual.dtype == expected.dtype == torch.float32
    stream = torch.cuda.Stream()
    stream.wait_stream(torch.cuda.current_stream())
    with torch.cuda.stream(stream):
        run('triton')
    torch.cuda.current_stream().wait_stream(stream)
    graph = torch.cuda.CUDAGraph()
    with torch.cuda.graph(graph, stream=stream):
        captured = run('triton')
    memory.add_(.25)
    locations.add_(.01)
    graph.replay()
    torch.cuda.synchronize()
    torch.testing.assert_close(captured, run('torch'), rtol=1e-4, atol=1e-5)


@pytest.mark.skipif(not torch.cuda.is_available(), reason='CUDA required')
def test_shared_value_preparation_preserves_reference_sampling(monkeypatch):
    from types import SimpleNamespace
    from engine.rtv4.dfine_decoder import TransformerDecoder
    shapes=[(7,9),(3,4),(1,2)]
    memory=torch.randn(2,77,10,device='cuda',dtype=torch.float16)
    locations=torch.rand(2,11,2,6,2,device='cuda')
    weights=torch.randn(2,11,2,6,device='cuda',dtype=torch.float16).softmax(-1)
    outputs=[]
    monkeypatch.setenv('DEFORM_ATTN_IMPL','torch')
    with torch.inference_mode(),torch.autocast('cuda',dtype=torch.float16):
        for mode in ['0','1']:
            monkeypatch.setenv('DEFORM_VALUE_CACHE',mode)
            value=TransformerDecoder.value_op(SimpleNamespace(num_head=2),memory,None,None,None,shapes)
            outputs.append(deformable_attention_core_func_v2(value,shapes,locations,weights,[2,3,1]))
            if mode=='1':assert all(v.is_contiguous() and v.dtype==torch.float32 for v in value)
    torch.testing.assert_close(outputs[0],outputs[1],rtol=0,atol=0)
