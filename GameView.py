import mss
import mss.tools
import numpy as np
import cv2
class GameView():
    def __init__(self):
        #Spring
        self.spring_template = cv2.imread('images/Spring.png', 0)
        self.spring_w, self.spring_h = self.spring_template.shape[::-1]
        self.last_springs = []



    def getScreen(self):
        with mss.mss() as sct:
            monitor = {"top": 247, "left": 727, "width": 448, "height": 682}
            output = "sct-{top}x{left}_{width}x{height}.png".format(**monitor)

            sct_img = sct.grab(monitor)
            frame = np.array(sct_img)
            return frame
    def getFullScreen(self):
        with mss.mss() as sct:
            monitor = {"top": 0, "left": 600, "width": 718, "height": 1078}
            output = "sct-{top}x{left}_{width}x{height}.png".format(**monitor)

            sct_img = sct.grab(monitor)
            frame = np.array(sct_img)
            return frame
    
    def preProcessImage(self, frame, target_size=None):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (3,3), 0)
        if target_size is not None:
            gray = cv2.resize(gray, target_size, interpolation=cv2.INTER_AREA)
        return gray
    
    def _iou(self, boxA, boxB):
        # box = (x1, y1, x2, y2, score)
        xA = max(boxA[0], boxB[0])
        yA = max(boxA[1], boxB[1])
        xB = min(boxA[2], boxB[2])
        yB = min(boxA[3], boxB[3])

        interArea = max(0, xB - xA) * max(0, yB - yA)
        boxAArea = (boxA[2] - boxA[0]) * (boxA[3] - boxA[1])
        boxBArea = (boxB[2] - boxB[0]) * (boxB[3] - boxB[1])

        iou = interArea / float(boxAArea + boxBArea - interArea + 1e-5)
        return iou

    def detectPlayer(self, frame):
        lower_yellow = np.array([20, 100, 100])
        upper_yellow = np.array([35, 255, 255])
        mask = cv2.inRange(frame, lower_yellow, upper_yellow)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            center = (x + w//2, y + h//2)
            return (x, y, w, h), center
        else:
            return None, None
    def detectPlatforms(self, frame):
        lower_green = np.array([34, 160, 150])
        upper_green = np.array([47, 234, 229])
        mask = cv2.inRange(frame, lower_green, upper_green)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            platforms = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                aspect_ratio = w / float(h)
                if area < 150:
                    continue
                if h > 20:
                    continue
                if aspect_ratio < 3.0:
                    continue

                platform = (x, y, w, h)
                platforms.append(platform)
            return platforms
        else:
            return []
        
    def detectSprings(self, frame, platforms):
        springs = []
        if not platforms:
            return springs

        gray = self.preProcessImage(frame)
        threshold = 0.6 
        
        # Expansion variables
        p_top, p_bot, p_side = 40, 20, 15

        for (px, py, pw, ph) in platforms:
            # 1. Define ROI
            s_top = max(0, py - p_top)
            s_bottom = py + ph + p_bot
            s_left = max(0, px - p_side)
            s_right = px + pw + p_side
            
            roi = gray[s_top:s_bottom, s_left:s_right]
            
            if roi.shape[0] < self.spring_h or roi.shape[1] < self.spring_w:
                continue

            # 2. Match Template
            res = cv2.matchTemplate(roi, self.spring_template, cv2.TM_CCOEFF_NORMED)
            
            # 3. Find ALL matches above threshold in this ROI
            y_locs, x_locs = np.where(res >= threshold)
            
            candidates = []
            for (x, y) in zip(x_locs, y_locs):
                # Map ROI coordinates back to full screen coordinates
                abs_x = s_left + x
                abs_y = s_top + y
                candidates.append((abs_x, abs_y, abs_x + self.spring_w, abs_y + self.spring_h, res[y, x]))

            # 4. Filter duplicates (Non-Maximum Suppression) within this ROI
            candidates = sorted(candidates, key=lambda b: b[4], reverse=True)
            while candidates:
                box = candidates.pop(0)
                # Convert back to (x, y, w, h) for final output
                springs.append((box[0], box[1], self.spring_w, self.spring_h))

                # Remove any other candidate that overlaps too much with the one we just saved
                candidates = [c for c in candidates if self._iou(box, c) < 0.3]
                
        return springs
    
    def detectPropellors(self, frame):
        lower_orange = np.array([5, 210, 200])
        upper_orange = np.array([15, 255, 255])
        mask = cv2.inRange(frame, lower_orange, upper_orange)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            center = (x + w//2, y + h//2)
            return (x-5, y-5, w+25, h+10), center
        else:
            return None, None
    
    def detectRockets(self, frame):
        lower_blue = np.array([88, 34, 195])
        upper_blue = np.array([92, 54, 215])
        mask = cv2.inRange(frame, lower_blue, upper_blue)

        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            area = w * h
            if area < 10:
                return None, None

            center = (x + w//2, y + h//2)
            return (x-35, y-20, w+55, h+35), center
        else:
            return None, None


    def detectMovingPlatforms(self, frame):
        lower_blue = np.array([90, 200, 180])
        upper_blue = np.array([100, 255, 255])
        mask = cv2.inRange(frame, lower_blue, upper_blue)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        moving_platforms = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            area = w * h
            aspect_ratio = w / float(h)

            if area < 150:
                continue
            if h > 20:
                continue
            if aspect_ratio < 3.0:
                continue

            moving_platforms.append((x, y, w, h))

        return moving_platforms

    def detectWhitePlatforms(self, frame):
        lower_white = np.array([0, 0, 254])
        upper_white = np.array([179, 1, 255])
        mask = cv2.inRange(frame, lower_white, upper_white)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            platforms = []
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                aspect_ratio = w / float(h)

                # Filter out noise / non-platforms
                if area < 150:
                    continue
                if h > 20:
                    continue
                if aspect_ratio < 3.0:
                    continue

                platform = (x, y, w, h)
                platforms.append(platform)
            return platforms
        else:
            return []
    
    def detectBlackHoles(self, frame, min_area=500):
        # Define black color range (low value, any hue/saturation)
        lower_black = np.array([0, 0, 0])
        upper_black = np.array([180, 255, 50])  # V <= 50

        # Create mask
        mask = cv2.inRange(frame, lower_black, upper_black)

        # Clean up noise
        kernel = np.ones((5,5), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        black_holes = []
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < min_area:
                continue  # skip small specks

            # Optional: approximate contour for smoother outline
            epsilon = 0.01 * cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, epsilon, True)

            black_holes.append(approx)

        return black_holes
    
    def detectBrownPlatforms(self, hsv_frame):
        # Brown in HSV is roughly Hue 8-20, Saturation 50-180, Value 50-180
        lower_brown = np.array([8, 50, 40])
        upper_brown = np.array([22, 210, 200])
        
        mask = cv2.inRange(hsv_frame, lower_brown, upper_brown)

        # Clean up the cracks inside the platform so it stays one solid box
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)

        # Find contours
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        platforms = []
        if contours:
            for contour in contours:
                x, y, w, h = cv2.boundingRect(contour)
                area = w * h
                aspect_ratio = w / float(h)

                if area < 300: 
                    continue
                
                if aspect_ratio < 2.0:
                    continue

                if h > 35:
                    continue

                platforms.append((x, y, w, h))
                
        return platforms

    def detectMonsters(self, hsv_frame, excluded_bboxes, player_center):
        # 1. Detect everything that isn't the background paper
        lower_paper = np.array([0, 0, 180]) 
        upper_paper = np.array([180, 60, 255])
        bg_mask = cv2.inRange(hsv_frame, lower_paper, upper_paper)
        not_paper_mask = cv2.bitwise_not(bg_mask)

        # 2. Specifically detect the Brown Platform color
        # Brown is Hue 8-22, Saturation 50-210, Value 40-200
        lower_brown = np.array([8, 50, 40])
        upper_brown = np.array([22, 210, 200])
        brown_mask = cv2.inRange(hsv_frame, lower_brown, upper_brown)

        # 3. SUBTRACT Brown from the Monster Mask
        # This removes brown pixels before findContours ever sees them
        mask = cv2.subtract(not_paper_mask, brown_mask)

        # Clean up noise
        kernel = np.ones((3,3), np.uint8)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel)
        
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        monster_boxes = []
        for cnt in contours:
            x, y, w, h = cv2.boundingRect(cnt)
            area = cv2.contourArea(cnt)

            # Standard Filters
            if area < 500 or area > 15000: continue
            aspect_ratio = float(w) / h
            if aspect_ratio > 2.2 or aspect_ratio < 0.4: continue

            # Overlap Exclusion (Player & Items)
            is_excluded = False
            if player_center:
                px, py = player_center
                if (x - 25 <= px <= x + w + 25) and (y - 25 <= py <= y + h + 25):
                    is_excluded = True

            for ex_box in excluded_bboxes:
                if ex_box is None: continue
                ex_x, ex_y, ex_w, ex_h = ex_box
                if (abs(x - ex_x) < 30 and abs(y - ex_y) < 30):
                    is_excluded = True
                    break
            
            if is_excluded: continue

            # Final check: Monsters are usually very saturated
            roi = hsv_frame[y:y+h, x:x+w]
            if np.mean(roi[:, :, 1]) < 60: continue

            monster_boxes.append((x, y, w, h))

        return monster_boxes