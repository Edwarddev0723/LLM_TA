import serial
import json

# 定義您的標籤列表（請根據您訓練模型時的順序填寫）
class_names = ["閉眼", "睜眼", "打哈欠", "不打哈欠"] 

# 初始化串口
ser = serial.Serial('/dev/cu.usbmodem578D0264891', 921600) # WE2 建議波特率設高一點以防數據堵塞

ser.reset_input_buffer()

# 啟動推論：持續執行, 輸出結果, 不顯示影像
command = "AT+INVOKE=-1,1,0\r\n"
ser.write(command.encode('utf-8'))

# 開始讀取結果
while True:
    line = ser.readline().decode('utf-8', errors='ignore').strip()
    if '"name":"INVOKE"' in line or '"boxes"' in line:
        # print(f"【成功獲取辨識數據】: {line}")
        try:
            obj = json.loads(line)
            boxes = obj['data'].get('boxes', [])
            
            if not boxes:
                print("尚未偵測到任何物體")
            else:
                for box in boxes:
                    # 取得最後一個位元作為標籤索引
                    label_index = box[-1] 
                    confidence = box[-2]
                    
                    label_name = class_names[label_index] if label_index < len(class_names) else f"未知({label_index})"
                    print(f"偵測到: {label_name}, 信心度: {confidence}%")
        except Exception as e:
            print(f"解析錯誤: {e}")

    elif "INIT@STAT" in line:
        print("系統僅在初始化狀態，嘗試重新發送指令...")
        ser.write(b"AT+INVOKE=-1,1,0\r\n")
