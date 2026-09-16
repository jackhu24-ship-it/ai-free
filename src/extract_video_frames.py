import sys
import os

# 尋找 OpenCV 或 imageio 或使用 ffmpeg
try:
    import cv2
    video_path = r"C:\Users\user\OneDrive\桌面\SS.mp4"
    if not os.path.exists(video_path):
        video_path = r"C:\Users\user\Desktop\SS.mp4"

    out_dir = r"G:\我的雲端硬碟\AI_master_workspace\three_memory\DATA\ss_frames"
    os.makedirs(out_dir, exist_ok=True)

    cap = cv2.VideoCapture(video_path)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    print(f"影片總幀數: {total_frames}")

    if total_frames > 0:
        step_ratios = [0.1, 0.3, 0.5, 0.7, 0.9, 0.98]
        for i, ratio in enumerate(step_ratios):
            target_f = int(total_frames * ratio)
            cap.set(cv2.CAP_PROP_POS_FRAMES, target_f)
            ret, frame = cap.read()
            if ret:
                save_path = os.path.join(out_dir, f"frame_{i+1}.png")
                cv2.imwrite(save_path, frame)
                print(f"已截圖第 {i+1} 張 (幀 {target_f}): {save_path}")
    cap.release()
except Exception as e:
    print(f"OpenCV 擷取失敗: {e}")
