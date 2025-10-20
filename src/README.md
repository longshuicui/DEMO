# 流程
1. 初始化 Controller
   * APP 启动
   * Agent 初始化
     * 日志模块
     * LLM模块
     * 上下文管理模块
     * 状态管理
2. APP触发Agent运行


# Binding
1. LLM模块
   * 输入：OpenAI兼容格式，此处需要判断模型是否支持工具