import cv2
import numpy as np
from sklearn.cluster import DBSCAN
from typing import Tuple, List, Optional, Set
from enum import Enum


class CoordinateSpace(Enum):
    """Coordinate space identifier."""
    ORIGINAL = "original"
    WARPED = "warped"


class GridDetector:
    """Detects and manages grid structure in images."""
    
    def __init__(
        self,
        grid_h_count: int,
        grid_w_count: int,
        adaptive_block_size: int = 55,
        adaptive_c: int = 7,
        morph_iterations: Tuple[int, int] = (2, 2),
        line_morph_iterations: Tuple[int, int] = (3, 2),
        dbscan_eps: int = 20,
        dbscan_min_samples: int = 3,
        min_cluster_size: int = 5,
        auto_perspective: bool = True,
        perspective_min_coverage: float = 0.6,
        debug: bool = False
    ):
        """
        Initialize grid detector with preprocessing parameters.
        
        Args:
            grid_h_count: Expected number of grid rows
            grid_w_count: Expected number of grid columns
            adaptive_block_size: Block size for adaptive threshold
            adaptive_c: Constant subtracted from mean in adaptive threshold
            morph_iterations: (erode, dilate) iterations for noise removal
            line_morph_iterations: (dilate, erode) iterations for line enhancement
            dbscan_eps: DBSCAN epsilon parameter for clustering
            dbscan_min_samples: DBSCAN minimum samples for core points
            min_cluster_size: Minimum cluster size to consider as valid grid line
            auto_perspective: If True, auto-detect and correct perspective before detection
            perspective_min_coverage: Minimum fraction of image dimensions the
                                      bounding rect must cover to trigger correction (0-1)
            debug: If True, show intermediate processing steps
        """
        self.grid_h_count = grid_h_count
        self.grid_w_count = grid_w_count
        self.adaptive_block_size = adaptive_block_size
        self.adaptive_c = adaptive_c
        self.morph_iterations = morph_iterations
        self.line_morph_iterations = line_morph_iterations
        self.dbscan_eps = dbscan_eps
        self.dbscan_min_samples = dbscan_min_samples
        self.min_cluster_size = min_cluster_size
        self.auto_perspective = auto_perspective
        self.perspective_min_coverage = perspective_min_coverage
        self.debug = debug

        self.x_grid: Optional[np.ndarray] = None
        self.y_grid: Optional[np.ndarray] = None
        self.image_shape: Optional[Tuple[int, int]] = None
        self.original_image: Optional[np.ndarray] = None
        self.warped_image: Optional[np.ndarray] = None
        # Perspective transform matrix (None if not applied)
        self.perspective_matrix: Optional[np.ndarray] = None
        self.warped_size: Optional[Tuple[int, int]] = None

    # ------------------------------------------------------------------
    # Debug helper
    # ------------------------------------------------------------------

    def _show_debug(self, title: str, image: np.ndarray, scale: float = 0.2):
        """Show debug image if debug mode is enabled."""
        if self.debug:
            resized = cv2.resize(image, None, fx=scale, fy=scale)
            cv2.imshow(title, resized)
            cv2.waitKey(0)

    # ------------------------------------------------------------------
    # Perspective correction
    # ------------------------------------------------------------------

    def _find_main_rect(self, image: np.ndarray) -> Optional[np.ndarray]:
        """
        Find the largest rotated rectangle that covers at least
        `perspective_min_coverage` of both image dimensions.

        Returns:
            Ordered corner points (4x2 float32) in [top-left, top-right,
            bottom-right, bottom-left] order, or None if not found.
        """
        try:
            img_h, img_w = image.shape[:2]
            min_w = img_w * self.perspective_min_coverage
            min_h = img_h * self.perspective_min_coverage

            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

            # Simple threshold to find the dominant object/table area
            binary = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY_INV,
                self.adaptive_block_size,
                self.adaptive_c
            )

            # Close small gaps so the outer border appears as one region
            kernel = np.ones((5, 5), np.uint8)
            closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=4)
            closed = cv2.dilate(closed, kernel, iterations=3)

            self._show_debug("Perspective - closed binary", closed)

            contours, _ = cv2.findContours(
                closed, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            best_box = None
            best_area = 0.0

            for cnt in contours:
                rect = cv2.minAreaRect(cnt)
                (cx, cy), (rw, rh), angle = rect

                # Ensure width >= height convention
                if rw < rh:
                    rw, rh = rh, rw

                if rw < min_w or rh < min_h:
                    continue

                box = cv2.boxPoints(rect).astype(np.float32)
                area = float(rw * rh)
                if area > best_area:
                    best_area = area
                    best_box = box

            if best_box is None:
                return None

            return self._order_points(best_box)

        except Exception:
            return None

    @staticmethod
    def _order_points(pts: np.ndarray) -> np.ndarray:
        """
        Sort four points into [top-left, top-right, bottom-right, bottom-left].
        """
        rect = np.zeros((4, 2), dtype=np.float32)

        s = pts.sum(axis=1)          # smallest sum  → top-left
        rect[0] = pts[np.argmin(s)]
        rect[2] = pts[np.argmax(s)]  # largest sum   → bottom-right

        diff = np.diff(pts, axis=1)  # smallest diff → top-right
        rect[1] = pts[np.argmin(diff)]
        rect[3] = pts[np.argmax(diff)]

        return rect

    def _perspective_correct(self, image: np.ndarray) -> np.ndarray:
        """
        Detect the main rectangle and apply perspective correction.
        Stores `perspective_matrix` and `warped_size` for later use.

        Returns the corrected image, or the original image unchanged if
        no suitable rectangle is found.
        """
        corners = self._find_main_rect(image)

        if corners is None:
            self.perspective_matrix = None
            self.warped_size = None
            return image

        tl, tr, br, bl = corners

        # Compute output dimensions from the detected rectangle
        width = int(max(
            np.linalg.norm(br - bl),
            np.linalg.norm(tr - tl)
        ))
        height = int(max(
            np.linalg.norm(tr - br),
            np.linalg.norm(tl - bl)
        ))

        if width <= 0 or height <= 0:
            self.perspective_matrix = None
            self.warped_size = None
            return image

        dst = np.array([
            [0,         0],
            [width - 1, 0],
            [width - 1, height - 1],
            [0,         height - 1],
        ], dtype=np.float32)

        self.perspective_matrix = cv2.getPerspectiveTransform(corners, dst)
        self.warped_size = (width, height)

        warped = cv2.warpPerspective(image, self.perspective_matrix, self.warped_size)

        if self.debug:
            debug_img = image.copy()
            cv2.polylines(
                debug_img,
                [corners.astype(np.int32)],
                isClosed=True,
                color=(0, 0, 255),
                thickness=5
            )
            self._show_debug("Perspective - detected rect", debug_img)
            self._show_debug("Perspective - corrected", warped)

        return warped

    def warp_point(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """
        Map a point from the original image space into the warped image space.

        Useful when you have coordinates in the original image and need to
        find which grid cell they fall into after perspective correction.

        Returns None if no perspective transform was applied.
        """
        if self.perspective_matrix is None:
            return None
        try:
            pt = np.array([[[float(x), float(y)]]], dtype=np.float32)
            warped = cv2.perspectiveTransform(pt, self.perspective_matrix)
            wx, wy = warped[0][0]
            return int(round(wx)), int(round(wy))
        except Exception:
            return None

    def unwarp_point(self, x: int, y: int) -> Optional[Tuple[int, int]]:
        """
        Map a point from the warped image space back to the original image space.

        Returns None if no perspective transform was applied.
        """
        if self.perspective_matrix is None:
            return None
        try:
            inv = np.linalg.inv(self.perspective_matrix)
            pt = np.array([[[float(x), float(y)]]], dtype=np.float32)
            original = cv2.perspectiveTransform(pt, inv)
            ox, oy = original[0][0]
            return int(round(ox)), int(round(oy))
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Detection pipeline
    # ------------------------------------------------------------------

    def detect(self, image: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[np.ndarray]]:
        """
        Detect grid lines in the input image.

        If `auto_perspective` is enabled (default), the method first attempts
        to find the main table/grid rectangle and flatten it via perspective
        transform before running the grid detection pipeline.

        Args:
            image: Input BGR image

        Returns:
            Tuple of (x_grid, y_grid) arrays containing grid line coordinates,
            or (None, None) if detection fails.
            Coordinates are relative to the (possibly warped) working image.
        """
        if image is None:
            return None, None

        # Store original image
        self.original_image = image.copy()

        # Perspective correction (optional but on by default)
        working = self._perspective_correct(image) if self.auto_perspective else image

        # Store warped image
        self.warped_image = working.copy()
        self.image_shape = working.shape[:2]

        # Grayscale
        gray = cv2.cvtColor(working, cv2.COLOR_BGR2GRAY)
        self._show_debug("1. Grayscale", gray)

        # Preprocess
        binary = self._preprocess(gray)
        if binary is None:
            return None, None
        self._show_debug("2. Binary (after preprocessing)", binary)

        # Extract rectangles
        rectangles = self._extract_rectangles(binary)
        if not rectangles:
            return None, None

        if self.debug:
            debug_img = working.copy()
            for rect in rectangles:
                cv2.polylines(debug_img, [rect], True, (0, 255, 0), 2)
            self._show_debug("3. Detected rectangles", debug_img)

        # Cluster into grid lines
        grid_result = self._cluster_grid_lines(rectangles)
        if grid_result is None:
            return None, None
        self.x_grid, self.y_grid = grid_result

        if self.debug:
            debug_img = working.copy()
            for y in self.y_grid:
                cv2.line(debug_img, (0, int(y)), (debug_img.shape[1], int(y)), (255, 0, 0), 2)
            for x in self.x_grid:
                cv2.line(debug_img, (int(x), 0), (int(x), debug_img.shape[0]), (255, 0, 0), 2)
            self._show_debug("4. Grid before outlier removal", debug_img)

        # Remove outliers
        self.x_grid = self._remove_outliers(self.x_grid)
        self.y_grid = self._remove_outliers(self.y_grid)

        if self.x_grid is None or self.y_grid is None:
            return None, None

        if self.debug:
            debug_img = working.copy()
            for y in self.y_grid:
                cv2.line(debug_img, (0, int(y)), (debug_img.shape[1], int(y)), (0, 255, 0), 3)
            for x in self.x_grid:
                cv2.line(debug_img, (int(x), 0), (int(x), debug_img.shape[0]), (0, 255, 0), 3)
            self._show_debug("5. Final grid", debug_img)

        return self.x_grid, self.y_grid

    # ------------------------------------------------------------------
    # Private pipeline steps
    # ------------------------------------------------------------------

    def _preprocess(self, gray: np.ndarray) -> Optional[np.ndarray]:
        """Apply preprocessing to extract grid structure."""
        try:
            binary = cv2.adaptiveThreshold(
                gray, 255,
                cv2.ADAPTIVE_THRESH_MEAN_C,
                cv2.THRESH_BINARY_INV,
                self.adaptive_block_size,
                self.adaptive_c
            )

            kernel = np.ones((3, 3), np.uint8)
            binary = cv2.erode(binary, kernel, iterations=self.morph_iterations[0])
            binary = cv2.dilate(binary, kernel, iterations=self.morph_iterations[1])

            kernel_v = np.ones((15, 1), np.uint8)
            binary = cv2.dilate(binary, kernel_v, iterations=self.line_morph_iterations[0])
            binary = cv2.erode(binary, kernel_v, iterations=self.line_morph_iterations[1])

            kernel_h = np.ones((1, 15), np.uint8)
            binary = cv2.dilate(binary, kernel_h, iterations=self.line_morph_iterations[0])
            binary = cv2.erode(binary, kernel_h, iterations=self.line_morph_iterations[1])

            return binary
        except Exception:
            return None

    def _extract_rectangles(self, binary: np.ndarray) -> List[np.ndarray]:
        """Extract rectangle contours from binary image."""
        try:
            contours, _ = cv2.findContours(
                binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE
            )

            img_h, img_w = binary.shape
            grid_w = img_w // self.grid_w_count
            grid_h = img_h // self.grid_h_count
            grid_area = grid_h * grid_w

            rectangles = []
            for contour in contours:
                rect = cv2.minAreaRect(contour)
                box = cv2.boxPoints(rect)
                box = np.int32(box)
                area = cv2.contourArea(box)
                if (grid_area / 2) < area < (grid_area * 2):
                    rectangles.append(box)

            return rectangles
        except Exception:
            return []

    def _cluster_grid_lines(
        self,
        rectangles: List[np.ndarray]
    ) -> Optional[Tuple[np.ndarray, np.ndarray]]:
        """Cluster rectangle coordinates into horizontal and vertical grid lines."""
        if not rectangles:
            return None

        try:
            points = np.vstack(rectangles)
            x_coords = points[:, 0].reshape(-1, 1)
            y_coords = points[:, 1].reshape(-1, 1)

            dbscan_x = DBSCAN(eps=self.dbscan_eps, min_samples=self.dbscan_min_samples).fit(x_coords)
            dbscan_y = DBSCAN(eps=self.dbscan_eps, min_samples=self.dbscan_min_samples).fit(y_coords)

            x_grid = self._extract_grid_from_clusters(x_coords, dbscan_x.labels_)
            y_grid = self._extract_grid_from_clusters(y_coords, dbscan_y.labels_)

            if not x_grid or not y_grid:
                return None

            x_grid.insert(0, 0)
            x_grid.append(self.image_shape[1] - 1)
            y_grid.insert(0, 0)
            y_grid.append(self.image_shape[0] - 1)

            return np.array(sorted(x_grid)), np.array(sorted(y_grid))
        except Exception:
            return None

    def _extract_grid_from_clusters(
        self,
        coordinates: np.ndarray,
        labels: np.ndarray
    ) -> List[int]:
        """Extract one representative coordinate per valid cluster."""
        grid = []
        try:
            for cluster_id in set(labels):
                if cluster_id == -1:
                    continue
                cluster_coords = coordinates[labels == cluster_id]
                if len(cluster_coords) >= self.min_cluster_size:
                    grid.append(int(cluster_coords.mean()))
        except Exception:
            pass
        return grid

    def _remove_outliers(self, grid: np.ndarray) -> Optional[np.ndarray]:
        """Remove outlier grid lines based on dominant spacing distribution."""
        if grid is None or len(grid) < 2:
            return None

        try:
            spacings = grid[1:] - grid[:-1]
            bin_size = max(50, int(spacings.std()))
            bins = np.arange(spacings.max()+5 , spacings.min()-5 , -bin_size)
            bins = bins[::-1]
            hist, edges = np.histogram(spacings, bins=bins)

            bin_idx = np.argmax(hist)
            lower = edges[bin_idx]
            upper = edges[bin_idx + 1]

            valid_indices = np.where((spacings >= lower) & (spacings < upper))[0].tolist()

            if not valid_indices:
                return None

            valid_indices.append(valid_indices[-1] + 1)

            return grid[valid_indices]
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Public query methods
    # ------------------------------------------------------------------

    def point_to_cell(
        self,
        x: int,
        y: int,
        space: CoordinateSpace = CoordinateSpace.ORIGINAL
    ) -> Optional[Tuple[int, int]]:
        """
        Get grid cell indices for a point.

        Args:
            x: X coordinate
            y: Y coordinate
            space: Whether coordinates are in ORIGINAL or WARPED image space

        Returns:
            (col_index, row_index), or None if grid is not detected.
        """
        if self.x_grid is None or self.y_grid is None:
            return None

        try:
            # Convert to warped space if needed
            if space == CoordinateSpace.ORIGINAL and self.perspective_applied:
                warped = self.warp_point(x, y)
                if warped is None:
                    return None
                x, y = warped

            col = int(np.clip(
                np.searchsorted(self.x_grid, x, side='right') - 1,
                0, len(self.x_grid) - 2
            ))
            row = int(np.clip(
                np.searchsorted(self.y_grid, y, side='right') - 1,
                0, len(self.y_grid) - 2
            ))
            return col, row
        except Exception:
            return None

    def box_to_cells(
        self,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        space: CoordinateSpace = CoordinateSpace.ORIGINAL,
        overlap_threshold: float = 0.0
    ) -> Optional[Set[Tuple[int, int]]]:
        """
        Get all grid cells that overlap with a bounding box.

        Args:
            x1, y1: One corner of the box
            x2, y2: Opposite corner of the box
            space: Whether coordinates are in ORIGINAL or WARPED image space
            overlap_threshold: Minimum cell-coverage ratio (0–1) to include a cell

        Returns:
            Set of (col_index, row_index) tuples, or None if grid is not detected.
        """
        if self.x_grid is None or self.y_grid is None:
            return None

        try:
            # Convert to warped space if needed
            if space == CoordinateSpace.ORIGINAL and self.perspective_applied:
                p1 = self.warp_point(x1, y1)
                p2 = self.warp_point(x2, y2)
                if p1 is None or p2 is None:
                    return None
                x1, y1 = p1
                x2, y2 = p2

            x_min, x_max = min(x1, x2), max(x1, x2)
            y_min, y_max = min(y1, y2), max(y1, y2)

            occupied: Set[Tuple[int, int]] = set()

            for row_idx in range(len(self.y_grid) - 1):
                for col_idx in range(len(self.x_grid) - 1):
                    cx1, cx2 = self.x_grid[col_idx], self.x_grid[col_idx + 1]
                    cy1, cy2 = self.y_grid[row_idx], self.y_grid[row_idx + 1]

                    ix1, ix2 = max(x_min, cx1), min(x_max, cx2)
                    iy1, iy2 = max(y_min, cy1), min(y_max, cy2)

                    if ix2 > ix1 and iy2 > iy1:
                        inter_area = (ix2 - ix1) * (iy2 - iy1)
                        cell_area = (cx2 - cx1) * (cy2 - cy1)
                        if cell_area > 0 and (inter_area / cell_area) > overlap_threshold:
                            occupied.add((col_idx, row_idx))

            return occupied
        except Exception:
            return None

    def draw_grid(
        self,
        image: np.ndarray,
        color: Tuple[int, int, int] = (0, 255, 0),
        thickness: int = 5
    ) -> Optional[np.ndarray]:
        """
        Draw detected grid lines on an image.

        Args:
            image: Image to draw on (will be copied)
            color: BGR line color
            thickness: Line thickness in pixels

        Returns:
            Annotated image copy, or None if grid is not detected.
        """
        if self.x_grid is None or self.y_grid is None or image is None:
            return None

        try:
            result = image.copy()
            for y in self.y_grid:
                y = int(y)
                result[y:y + thickness, :] = color
            for x in self.x_grid:
                x = int(x)
                result[:, x:x + thickness] = color
            return result
        except Exception:
            return None

    def draw_point(
        self,
        image: np.ndarray,
        x: int,
        y: int,
        space: CoordinateSpace = CoordinateSpace.ORIGINAL,
        color: Tuple[int, int, int] = (0, 0, 255),
        radius: int = 10,
        thickness: int = -1
    ) -> Optional[np.ndarray]:
        """
        Draw a point on an image.

        Args:
            image: Image to draw on (will be copied)
            x: X coordinate
            y: Y coordinate
            space: Whether coordinates are in ORIGINAL or WARPED image space
            color: BGR color
            radius: Circle radius
            thickness: Line thickness (-1 for filled)

        Returns:
            Annotated image copy, or None on error.
        """
        if image is None:
            return None

        try:
            result = image.copy()
            
            # No conversion needed - draw directly
            cv2.circle(result, (int(x), int(y)), radius, color, thickness)
            
            return result
        except Exception:
            return None


    def convert_cell2real(self,point):
        cell = point

        first = cell[0] + 1
        second = cell[1] + 1

        result = (chr(first + 96),int(second))
        print(result)

        return result




    def draw_box(
        self,
        image: np.ndarray,
        x1: int,
        y1: int,
        x2: int,
        y2: int,
        space: CoordinateSpace = CoordinateSpace.ORIGINAL,
        color: Tuple[int, int, int] = (255, 0, 0),
        thickness: int = 3
    ) -> Optional[np.ndarray]:
        """
        Draw a bounding box on an image.

        Args:
            image: Image to draw on (will be copied)
            x1, y1: One corner
            x2, y2: Opposite corner
            space: Whether coordinates are in ORIGINAL or WARPED image space
            color: BGR color
            thickness: Line thickness

        Returns:
            Annotated image copy, or None on error.
        """
        if image is None:
            return None

        try:
            result = image.copy()
            
            # No conversion needed - draw directly
            cv2.rectangle(result, (int(x1), int(y1)), (int(x2), int(y2)), color, thickness)
            
            return result
        except Exception:
            return None

    # ------------------------------------------------------------------
    # Image getters
    # ------------------------------------------------------------------

    def get_original_image(self) -> Optional[np.ndarray]:
        """Get the original input image."""
        return self.original_image.copy() if self.original_image is not None else None

    def get_warped_image(self) -> Optional[np.ndarray]:
        """Get the perspective-corrected image (or original if no correction was applied)."""
        return self.warped_image.copy() if self.warped_image is not None else None

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def grid_shape(self) -> Optional[Tuple[int, int]]:
        """Grid dimensions as (num_cols, num_rows)."""
        if self.x_grid is None or self.y_grid is None:
            return None
        return len(self.x_grid) - 1, len(self.y_grid) - 1

    @property
    def is_detected(self) -> bool:
        """True if the grid has been successfully detected."""
        return self.x_grid is not None and self.y_grid is not None

    @property
    def perspective_applied(self) -> bool:
        """True if a perspective correction was applied during the last detect() call."""
        return self.perspective_matrix is not None


# ================= USAGE EXAMPLE =================

if __name__ == "__main__":
    detector = GridDetector(10, 22, debug=False)

    image = cv2.imread("2.jpg")
    if image is None:
        print("تصویر پیدا نشد")
        exit()

    x_grid, y_grid = detector.detect(image)

    if detector.is_detected:
        print(f"شبکه شناسایی شد: {detector.grid_shape[0]} ستون × {detector.grid_shape[1]} ردیف")
        print(f"تصحیح perspective اعمال شد: {detector.perspective_applied}")

        # Get both images
        original_img = detector.get_original_image()
        warped_img = detector.get_warped_image()

        # Example 1: Point on ORIGINAL image
        point_orig = (480, 950)
        cell = detector.point_to_cell(*point_orig, space=CoordinateSpace.ORIGINAL)
        if cell:
            print(f"نقطه {point_orig} (روی عکس اصلی) در سلول {cell} قرار دارد")

        # Example 2: Point on WARPED image
        point_warped = (300, 500)
        cell = detector.point_to_cell(*point_warped, space=CoordinateSpace.WARPED)
        if cell:
            print(f"نقطه {point_warped} (روی عکس صاف‌شده) در سلول {cell} قرار دارد")

        # Example 3: Box on ORIGINAL image
        cells = detector.box_to_cells(100, 100, 600, 400, space=CoordinateSpace.WARPED, overlap_threshold=0.1)
        if cells:
            print(f"جعبه (روی عکس اصلی) با {len(cells)} سلول همپوشانی دارد")

        # Draw grid on warped image
        warped_with_grid = detector.draw_grid(warped_img)

        # Draw point on original image
        original_with_point = detector.draw_point(original_img, *point_orig, space=CoordinateSpace.ORIGINAL)

        # Draw box on original image
        warped_with_box = detector.draw_box(warped_with_grid, 100, 100, 600, 400, space=CoordinateSpace.WARPED)

        # Draw point on warped image
        warped_with_point = detector.draw_point(warped_with_box, *point_warped, space=CoordinateSpace.WARPED)

        # Display results
        if warped_with_point is not None:
            cv2.imshow("تصویر صاف‌شده با grid و نقطه", cv2.resize(warped_with_point, None, fx=0.2, fy=0.2))
        
        # if original_with_box is not None:
        #     cv2.imshow("تصویر اصلی با نقطه و جعبه", cv2.resize(original_with_box, None, fx=0.2, fy=0.2))
        
        cv2.waitKey(0)
    else:
        print("شناسایی شبکه ناموفق بود")

    cv2.destroyAllWindows()
