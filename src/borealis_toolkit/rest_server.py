import os

import uvicorn


def main() -> None:
    uvicorn.run(
        "borealis_toolkit.rest_api:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", "8000")),
        reload=False,
    )


if __name__ == "__main__":
    main()
