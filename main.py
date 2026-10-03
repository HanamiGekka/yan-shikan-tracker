from yan_shikan_tracker.main import main


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n收到程序级 Ctrl+C，研时记先退出啦喵。")
