import cv2


def extract_frames(video_path, max_frames=18):

    frames = []
    video_capture = cv2.VideoCapture(video_path)

    width = video_capture.get(cv2.CAP_PROP_FRAME_WIDTH)
    height = video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT)

    new_width = 640
    new_height = 480
    if not video_capture.isOpened():
        print(f"Error: Could not open video file {video_path}")
        return frames

    fps = video_capture.get(cv2.CAP_PROP_FPS)  # Получаем частоту кадров
    total_frames = int(video_capture.get(cv2.CAP_PROP_FRAME_COUNT))  # Общее количество кадров
    total_time = total_frames / fps  # Общее время видео в секундах

    if total_time <= max_frames:
        # Если видео меньше или равно 18 секунд, берем кадры каждую секунду
        frame_indices = [int(i * fps) for i in range(int(total_time))]
    else:
        # Если видео больше 18 секунд, рассчитываем интервал
        interval = total_time / max_frames
        frame_indices = [int(i * interval * fps) for i in range(max_frames)]

    for index in frame_indices:
        video_capture.set(cv2.CAP_PROP_POS_FRAMES, index)

        ret, frame = video_capture.read()
        if width > new_width or height > new_height:
            frame = cv2.resize(frame, (new_width, new_height))
        if ret:
            frames.append(frame)
        else:
            break

    frames_for_text = []
    desired_fps = 2  # Желаемая частота кадров в секунду
    frame_interval = int(round(fps / desired_fps))  # Интервал между кадрами

    for frame_index in range(0, total_frames, frame_interval):
        video_capture.set(cv2.CAP_PROP_POS_FRAMES, frame_index)
        ret, frame = video_capture.read()

        if width > new_width or height > new_height:
            frame = cv2.resize(frame, (new_width, new_height))
        if ret:
            frames_for_text.append(frame)
        else:
            break

    video_capture.release()
    return frames, frames_for_text, total_time
