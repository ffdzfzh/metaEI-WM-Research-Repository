import cv2
import numpy as np
import math
from pathlib import Path


def recognize_and_estimate_pose():
    demo_dir = Path(__file__).resolve().parent
    template_path = demo_dir / 'image_match' / 'IMS1.jpg'
    scene_path = demo_dir / 'image' / 'scene1_IMS.jpg'

    img_template = cv2.imread(template_path, cv2.IMREAD_GRAYSCALE)
    img_scene = cv2.imread(scene_path, cv2.IMREAD_GRAYSCALE)

    if img_template is None or img_scene is None:
        print("Unable to read the template or scene image.")
        return

    orb = cv2.ORB_create(nfeatures=2000)
    kp_template, des_template = orb.detectAndCompute(img_template, None)
    kp_scene, des_scene = orb.detectAndCompute(img_scene, None)

    bf = cv2.BFMatcher(cv2.NORM_HAMMING)
    matches = bf.knnMatch(des_scene, des_template, k=2)

    good_matches = []
    ratio_threshold = 0.75
    for m, n in matches:
        if m.distance < ratio_threshold * n.distance:
            good_matches.append(m)

    print(f"Candidate matches after the ratio test: {len(good_matches)}")

    MIN_MATCH_COUNT = 10
    if len(good_matches) > MIN_MATCH_COUNT:
        src_pts = np.float32([kp_scene[m.queryIdx].pt for m in good_matches]).reshape(-1, 1, 2)
        dst_pts = np.float32([kp_template[m.trainIdx].pt for m in good_matches]).reshape(-1, 1, 2)

        H, mask = cv2.findHomography(dst_pts, src_pts, cv2.RANSAC, 5.0)

        matchesMask = mask.ravel().tolist()
        inlier_count = sum(matchesMask)
        print(f"RANSAC inliers: {inlier_count}")

        if H is not None:
            h, w = img_template.shape
            pts = np.float32([[0, 0], [0, h - 1], [w - 1, h - 1], [w - 1, 0]]).reshape(-1, 1, 2)

            dst = cv2.perspectiveTransform(pts, H)

            img_scene_color = cv2.cvtColor(img_scene, cv2.COLOR_GRAY2BGR)
            img_scene_color = cv2.polylines(img_scene_color, [np.int32(dst)], True, (0, 255, 0), 3, cv2.LINE_AA)

            theta = math.atan2(H[1, 0], H[0, 0])
            angle_degrees = math.degrees(theta)

            print(f"IMS detected; estimated in-plane rotation: {angle_degrees:.2f} degrees")

            draw_params = dict(matchColor=(0, 255, 0),
                               singlePointColor=None,
                               matchesMask=matchesMask,
                               flags=2)

            img_result = cv2.drawMatches(img_scene, kp_scene, img_template, kp_template, good_matches, None,
                                         **draw_params)

            cv2.imshow("Recognition and Pose Estimation", img_scene_color)
            cv2.imshow("Matches", img_result)
            cv2.waitKey(0)
            cv2.destroyAllWindows()
        else:
            print("Homography estimation failed.")
    else:
        print(f"Insufficient matches: need more than {MIN_MATCH_COUNT}, found {len(good_matches)}.")


if __name__ == "__main__":
    recognize_and_estimate_pose()
