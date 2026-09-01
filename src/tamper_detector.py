"""
Trinetra AI - Tamper Detector v1
Person 1: AI / Document Forensics

Rule-based forensic checks using OpenCV.

Checks:
1. Image quality
2. Region analysis
3. Compression/noise
4. Copy-move/self-similarity heuristic
5. Visual/MRZ consistency

This module does NOT implement the risk engine.
"""

import os

import cv2
import numpy as np


# ============================================================
# 1. IMAGE QUALITY
# ============================================================

def check_image_quality(img: np.ndarray) -> dict:
    """
    Check image sharpness and exposure.

    Sharpness:
        Laplacian variance.

    Exposure:
        Uses the percentage of extremely dark and extremely
        bright pixels rather than global mean intensity.

    This is more appropriate for documents such as passports,
    which naturally contain large white/light-colored regions.
    """

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    # --------------------------------------------------------
    # Sharpness
    # --------------------------------------------------------

    laplacian_var = cv2.Laplacian(
        gray,
        cv2.CV_64F
    ).var()

    is_blurry = laplacian_var < 100.0

    # --------------------------------------------------------
    # Exposure
    # --------------------------------------------------------

    total_pixels = gray.size

    dark_clip_ratio = float(
        np.sum(gray < 30) / total_pixels
    )

    bright_clip_ratio = float(
        np.sum(gray > 250) / total_pixels
    )

    # A document can naturally have a bright background.
    # Therefore we only flag exposure when a substantial
    # portion of the image is near clipping.
    is_underexposed = dark_clip_ratio > 0.20
    is_overexposed = bright_clip_ratio > 0.20

    score = 100.0
    reasons = []

    # --------------------------------------------------------
    # Score
    # --------------------------------------------------------

    if is_blurry:
        score -= 40.0

        reasons.append(
            "Image is blurry (low sharpness variance)."
        )

    if is_underexposed:
        score -= 30.0

        reasons.append(
            "Image contains an unusually large "
            "underexposed/dark region."
        )

    if is_overexposed:
        score -= 30.0

        reasons.append(
            "Image contains an unusually large "
            "overexposed/bright clipped region."
        )

    return {
        "score": round(
            max(0.0, score),
            2
        ),

        "status": (
            "PASS"
            if score >= 70.0
            else "REVIEW"
        ),

        "details": {
            "laplacian_variance": round(
                float(laplacian_var),
                2
            ),

            "dark_clip_ratio": round(
                dark_clip_ratio,
                4
            ),

            "bright_clip_ratio": round(
                bright_clip_ratio,
                4
            ),
        },

        "reasons": reasons,
    }
def check_region_analysis(img: np.ndarray) -> dict:
    """
    Analyze edge density across document regions.

    This is a heuristic indicator only.
    It is NOT a definitive forgery detector.
    """

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    edges = cv2.Canny(
        gray,
        100,
        200
    )

    h, w = gray.shape

    # Divide image into a 2x2 grid.
    regions = {
        "top_left": edges[:h // 2, :w // 2],
        "top_right": edges[:h // 2, w // 2:],
        "bottom_left": edges[h // 2:, :w // 2],
        "bottom_right": edges[h // 2:, w // 2:],
    }

    densities = {}

    for name, region in regions.items():
        densities[name] = float(
            np.mean(region > 0)
        )

    overall_density = float(
        np.mean(edges > 0)
    )

    # Compare regions against the document's own average.
    region_values = np.array(
        list(densities.values()),
        dtype=np.float32
    )

    region_std = float(np.std(region_values))

    score = 90.0
    status = "PASS"
    reasons = []

    # Extremely sparse document.
    if overall_density < 0.01:
        score -= 40.0
        status = "REVIEW"

        reasons.append(
            "Unusually low edge density detected."
        )

    # Very uneven regions can indicate unusual local structure,
    # but this is only a heuristic.
    if region_std > 0.03:
        score -= 20.0

        if status == "PASS":
            status = "REVIEW"

        reasons.append(
            "Large variation in edge density between document regions."
        )

    return {
        "score": round(max(0.0, score), 2),
        "status": status,
        "details": {
            "overall_edge_density": round(
                overall_density,
                4
            ),
            "regional_edge_density": {
                k: round(v, 4)
                for k, v in densities.items()
            },
            "regional_std": round(
                region_std,
                4
            ),
        },
        "reasons": reasons,
    }


# ============================================================
# 3. COMPRESSION / NOISE
# ============================================================

def check_compression_noise(img: np.ndarray) -> dict:
    """
    Estimate local intensity variance.

    Important:
    Convert the image to float32 before squaring.
    This avoids uint8 overflow.
    """

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # FIX:
    # uint8 ** 2 can overflow.
    gray_float = gray.astype(np.float32)

    local_mean = cv2.blur(
        gray_float,
        (5, 5)
    )

    local_sq_mean = cv2.blur(
        gray_float ** 2,
        (5, 5)
    )

    local_variance = (
        local_sq_mean
        - local_mean ** 2
    )

    # Numerical precision can occasionally produce tiny
    # negative values.
    local_variance = np.maximum(
        local_variance,
        0
    )

    avg_noise = float(
        np.mean(local_variance)
    )

    score = 85.0
    status = "PASS"
    reasons = []

    if avg_noise < 2.0:
        score = 60.0
        status = "REVIEW"

        reasons.append(
            "Abnormally smooth local noise profile detected."
        )

    return {
        "score": round(score, 2),
        "status": status,
        "details": (
            f"Average local intensity variance: "
            f"{avg_noise:.2f}"
        ),
        "reasons": reasons,
    }


# ============================================================
# 4. COPY-MOVE / SELF-SIMILARITY
# ============================================================

def check_copy_move(img: np.ndarray) -> dict:
    """
    Lightweight copy-move/self-similarity heuristic.

    This is intentionally conservative for v1.

    Instead of comparing the entire left half against the
    entire right half, compare smaller patches at multiple
    locations.

    A high similarity between distant patches can be a
    suspicious indicator, but is NOT proof of tampering.
    """

    gray = cv2.cvtColor(
        img,
        cv2.COLOR_BGR2GRAY
    )

    # Downscale for performance.
    small = cv2.resize(
        gray,
        (256, 256),
        interpolation=cv2.INTER_AREA
    )

    h, w = small.shape

    patch_size = 32
    stride = 32

    patches = []

    for y in range(
        0,
        h - patch_size + 1,
        stride
    ):
        for x in range(
            0,
            w - patch_size + 1,
            stride
        ):
            patch = small[
                y:y + patch_size,
                x:x + patch_size
            ]

            patches.append(
                (x, y, patch)
            )

    best_similarity = 0.0
    best_pair = None

    for i in range(len(patches)):
        x1, y1, p1 = patches[i]

        for j in range(i + 1, len(patches)):
            x2, y2, p2 = patches[j]

            # Ignore nearby patches.
            distance = np.sqrt(
                (x1 - x2) ** 2
                + (y1 - y2) ** 2
            )

            if distance < 64:
                continue

            # Normalize each patch.
            p1_float = p1.astype(np.float32)
            p2_float = p2.astype(np.float32)

            p1_std = float(p1_float.std())
            p2_std = float(p2_float.std())

            # Flat patches aren't useful for copy-move detection.
            if p1_std < 5.0 or p2_std < 5.0:
                continue

            correlation = np.corrcoef(
                p1_float.flatten(),
                p2_float.flatten()
            )[0, 1]

            if np.isnan(correlation):
                continue

            if correlation > best_similarity:
                best_similarity = float(correlation)
                best_pair = (
                    (x1, y1),
                    (x2, y2)
                )

    score = 95.0
    status = "PASS"
    reasons = []

    # Conservative threshold.
    if best_similarity > 0.97:
        score = 45.0
        status = "SUSPECT"

        reasons.append(
            "Very high similarity detected between "
            "distant image patches."
        )

    return {
        "score": round(score, 2),
        "status": status,
        "details": {
            "max_patch_correlation": round(
                best_similarity,
                4
            ),
            "matched_patch_locations": best_pair,
        },
        "reasons": reasons,
    }


# ============================================================
# 5. VISUAL / MRZ CONSISTENCY
# ============================================================

def check_visual_mrz_consistency(
    validation_result: dict = None
) -> dict:
    """
    Reuse the existing cross-validation result.

    Expected validator structure:

    {
        "matches": 5,
        "total": 5,
        "all_match": True,
        "results": [...]
    }
    """

    if not validation_result:
        return {
            "score": 50.0,
            "status": "MISSING",
            "details": "No validation result provided.",
            "reasons": [
                "Missing document validation pipeline input."
            ],
        }

    matches = validation_result.get(
        "matches",
        0
    )

    total = validation_result.get(
        "total",
        0
    )

    all_match = validation_result.get(
        "all_match",
        False
    )

    # Support the older form as well, if it is ever passed.
    if "status" in validation_result:
        all_match = (
            validation_result.get("status") == "PASS"
        )

    if total > 0:
        match_ratio = matches / total
    else:
        match_ratio = 0.0

    if all_match:
        score = 100.0
        status = "PASS"
        reasons = []

    elif match_ratio >= 0.8:
        score = 70.0
        status = "REVIEW"
        reasons = [
            f"Most document fields match, "
            f"but validation is incomplete: "
            f"{matches}/{total}."
        ]

    else:
        score = 40.0
        status = "REVIEW"
        reasons = [
            f"Document field consistency failed: "
            f"{matches}/{total}."
        ]

    return {
        "score": round(score, 2),
        "status": status,
        "details": {
            "matches": matches,
            "total": total,
            "all_match": all_match,
            "match_ratio": round(
                match_ratio,
                2
            ),
        },
        "reasons": reasons,
    }


# ============================================================
# MAIN ANALYZER
# ============================================================

def analyze_tamper(
    image_path: str,
    validation_result: dict = None
) -> dict:
    """
    Run all five tamper/forensic checks.

    This function deliberately does NOT implement the
    project's risk engine.
    """

    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"Image path not found: {image_path}"
        )

    img = cv2.imread(image_path)

    if img is None:
        raise ValueError(
            f"Failed to read image from path: {image_path}"
        )

    checks = {
        "image_quality": check_image_quality(img),

        "region_analysis": check_region_analysis(img),

        "compression_noise": check_compression_noise(img),

        "copy_move": check_copy_move(img),

        "visual_mrz_consistency":
            check_visual_mrz_consistency(
                validation_result
            ),
    }

    scores = [
        check["score"]
        for check in checks.values()
        if check["status"] != "MISSING"
    ]

    average_score = (
        sum(scores) / len(scores)
        if scores
        else 0.0
    )

    failed_checks = [
        name
        for name, check in checks.items()
        if check["status"] in {
            "REVIEW",
            "SUSPECT"
        }
    ]

    # Conservative v1 decision.
    tamper_suspected = (
        len(failed_checks) >= 2
        or average_score < 70.0
    )

    if average_score >= 85.0 and not tamper_suspected:
        forensic_status = "CLEAN"

    elif average_score >= 65.0:
        forensic_status = "REVIEW"

    else:
        forensic_status = "SUSPICIOUS"

    all_reasons = []

    for name, check in checks.items():
        for reason in check.get(
            "reasons",
            []
        ):
            all_reasons.append(
                f"[{name}] {reason}"
            )

    return {
        "tamper_suspected": tamper_suspected,

        "tamper_score": round(
            average_score,
            2
        ),

        "forensic_status": forensic_status,

        "failed_checks": failed_checks,

        "checks": checks,

        "reasons": all_reasons,
    }