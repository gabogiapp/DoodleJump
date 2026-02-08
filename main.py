from GameView import GameView
import time
import cv2


def main():
    window_name = "Doodle Detection"
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.setWindowProperty(window_name, cv2.WND_PROP_TOPMOST, 1)

    game = GameView()
    frame_count = 0
    last_player_pos = None

    # Cache for low priority items
    lp_data = {
        "brown_platforms": [],
        "black_holes": [],
        "rocket": None,
        "propellor" : None
    }

    while True:
        start_time = time.time()
        frame = game.getScreen()
        if frame is None: continue
        coloredFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        frame_count += 1

        # 1. Low Priority Detection:
        if frame_count % 4 == 0:
            lp_data["black_holes"] = game.detectBlackHoles(coloredFrame)
            lp_data["rocket"], _ = game.detectRockets(coloredFrame)
            lp_data["propellor"], _ = game.detectPropellors(coloredFrame)

        # 2. High Priority Detection:
        player_bbox, player_center = game.detectPlayer(coloredFrame)
        if last_player_pos and player_center:
            # Calculate velocity manually for the AI
            vel_x = player_center[0] - last_player_pos[0]
            vel_y = player_center[1] - last_player_pos[1]
        else:
            vel_x, vel_y = 0, 0

        last_player_pos = player_center
        moving_platforms_boxes = game.detectMovingPlatforms(coloredFrame)
        blank_platforms_boxes = game.detectWhitePlatforms(coloredFrame)
        static_platforms_boxes = game.detectPlatforms(coloredFrame)
        springs = game.detectSprings(coloredFrame, static_platforms_boxes + moving_platforms_boxes)

        to_exclude = [player_bbox, lp_data["propellor"], lp_data["rocket"]]
        if to_exclude:
            to_exclude.extend(static_platforms_boxes)
            to_exclude.extend(moving_platforms_boxes)
            to_exclude.extend(springs)
        monsters_bboxes = game.detectMonsters(coloredFrame, to_exclude, player_center)

        # --- VISUALIZATION ---
        # Draw High Priority first
        if player_bbox:
            draw_labeled_box(frame, player_bbox, "Player", (0, 255, 0))

        for bbox in monsters_bboxes:
            draw_labeled_box(frame, bbox, "MONSTER", (0, 165, 255), thickness=3)

        for bbox in moving_platforms_boxes:
            draw_labeled_box(frame, bbox, "Moving", (255, 0, 255))

        for bbox in blank_platforms_boxes:
            draw_labeled_box(frame, bbox, "Blank", (255, 255, 255))

        for bbox in static_platforms_boxes:
            draw_labeled_box(frame, bbox, "", (0, 0, 255), 2)

        for bbox in springs:
            draw_labeled_box(frame, bbox, "Spring", (0, 0, 255), 1)

        if lp_data["rocket"]:
            bbox = lp_data["rocket"]
            draw_labeled_box(frame, bbox, "Rocket", (0, 0, 255), 1)

        if lp_data["propellor"]:
            bbox = lp_data["propellor"]
            draw_labeled_box(frame, bbox, "Propellor", (0, 0, 255), 1)

        draw_black_holes(frame, lp_data["black_holes"])

        cv2.imshow(window_name, frame)
        elapsed = (time.time() - start_time) * 1000
        print(f"Elapsed: {elapsed:.2f}ms")
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cv2.destroyAllWindows()

def draw_labeled_box(frame, bbox, label, color, thickness=2):
    x, y, w, h = bbox
    cv2.rectangle(frame, (x, y), (x + w, y + h), color, thickness)
    cv2.putText(frame, label, (x, y - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)

def draw_black_holes(frame, contours, label="Black Hole", color=(0, 0, 255), thickness=2):
    for cnt in contours:
        cv2.drawContours(frame, [cnt], -1, color, thickness)
        x, y, w, h = cv2.boundingRect(cnt)
        cv2.putText(frame, label, (x, y - 10),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)



if __name__ == "__main__":
    main()
