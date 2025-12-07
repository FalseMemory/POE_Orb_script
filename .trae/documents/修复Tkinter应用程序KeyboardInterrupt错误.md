## 问题分析

Terminal#776-791显示的是一个KeyboardInterrupt错误，当用户在终端中按Ctrl+C时，Tkinter应用程序会崩溃并显示完整的错误堆栈。这是因为Tkinter的`mainloop()`默认不处理KeyboardInterrupt异常。

## 解决方案

修改`main()`函数，在`root.mainloop()`周围添加异常处理，以捕获KeyboardInterrupt并优雅退出，避免显示错误堆栈。

## 实现步骤

1. **修改main函数**：在`e:\POE_script\src\ui\washer_gui.py`文件中，修改`main()`函数，添加try-except块来捕获KeyboardInterrupt
2. **添加优雅退出逻辑**：确保程序在捕获到KeyboardInterrupt时能够正确关闭所有资源并退出
3. **测试修复效果**：运行程序并按Ctrl+C，验证是否不再显示错误堆栈

## 代码修改

```python
def main():
    """
    主函数
    """
    # 创建根窗口
    root = tk.Tk()
    
    # 创建并运行GUI
    app = PoeWasherGUI(root)
    
    # 运行主循环，添加异常处理以捕获KeyboardInterrupt
    try:
        root.mainloop()
    except KeyboardInterrupt:
        # 捕获Ctrl+C，优雅退出
        print("\n程序已通过Ctrl+C停止")
        root.destroy()
```

## 预期效果

* 当用户按Ctrl+C时，程序会显示"程序已通过Ctrl+C停止"并优雅退出

* 不再显示完整的错误堆栈

* 所有资源会被正确释放

## 其他考虑

* 这个修复不会影响程序的正常功能

* 这是Tkinter应用程序处理KeyboardInterrupt的标准做法

* 修复后程序会

