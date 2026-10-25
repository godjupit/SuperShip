# 默认入口完整三轮确认

状态planned，Codex /root，GPU0 RTX4090独占；实际调用bash benchmark_optimized.sh，清除外部性能参数覆盖，使用新默认三项组合。实际环境只显式给PYTHON_BIN、OUTPUT_FILE和独立TRITON_CACHE_DIR；其他默认值从wrapper提取记录在config.json。随后完整验证集重测。通过检查后正式提交，较慢时恢复最快有效完整三轮日志。
