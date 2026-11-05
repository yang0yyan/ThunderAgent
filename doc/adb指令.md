- 重置ADB服务
  - adb kill-server
  - adb start-server
  - adb devices

- 连接机器
  - adb connect 127.0.0.1:16384

- 查找包名
  - adb shell pm list packages
- 查找包名（可筛选）
  - adb shell pm list packages | findstr "关键词"
- 查看第三方应用
  - adb shell pm list packages -3

- 获取启动 Activity
  - adb shell cmd package resolve-activity --brief <你的包名>

- 启动应用
  - adb shell am start -n <包名>/<Activity名>
- 停止应用
  - adb shell am force-stop <包名>

- 雷霆战机
  - com.a5game.ltzj.jj/com.xxx.sdk.GamePrivacyActivity