from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    LLM_BASE_URL: str = "http://localhost:8085/v1"
    LLM_MODEL_NAME: str = "Qwen3.6-35B-A3B-UD-Q4_K_M.gguf"
    DATABASE_URL: str = "sqlite:///./cost_estimator.db"
    LLM_TIMEOUT: int = 30 # seconds


    # # Image Processing
    # GRAYSCALE_THRESHOLD: int = 128
    # CANNY_LOW_THRESHOLD: int = 50
    # CANNY_HIGH_THRESHOLD: int = 150
    # HOUGH_RHO: int = 1
    # HOUGH_THETA: Decimal = 3.14159 / 180
    # HOUGH_THRESHOLD: int = 50
    # HOUGH_MIN_LINE_LENGTH: int = 30
    # HOUGH_MAX_LINE_GAP: int = 10

    # # Geometry Processing
    # LINE_MERGE_DISTANCE: int = 15  # Pixels
    # SNAP_DISTANCE: int = 10        # Pixels

    # # Export Settings
    # WALL_HEIGHT: int = 250         # cm
    # WALL_THICKNESS: int = 10       # cm
    # DEFAULT_ROOM_FLOOR_COLOR: str = "#FFFFFF"

    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()