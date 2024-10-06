# Copyright (c) Kuba Szczodrzyński 2024-10-03.

import uvicorn

if __name__ == "__main__":
    from .mdserver import app

    uvicorn.run(app, host="0.0.0.0")
