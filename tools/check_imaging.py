"""Check the Imaging service and events on a camera.

Usage:
    python3 check_imaging.py 192.168.2.2 80 admin PASSWORD

Shows how the camera answers GetOptions, GetImagingSettings and
CreatePullPointSubscription. The output explains why the night mode and
autofocus switches were not created.

No dependencies: soap.py from custom_components/onvif_ptz is reused.
"""

import asyncio
import logging
import sys
from pathlib import Path

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "custom_components" / "onvif_ptz")
)
from soap import OnvifError, OnvifPtzClient

logging.basicConfig(level=logging.DEBUG, format="%(levelname)s %(message)s")


async def main() -> None:
    if len(sys.argv) != 5:
        print(__doc__)
        sys.exit(1)

    host, port, user, password = sys.argv[1], int(sys.argv[2]), sys.argv[3], sys.argv[4]
    client = OnvifPtzClient(host, port, user, password)

    try:
        await client.async_setup()
        print("\n=== Discovered ===")
        print("model:          ", client.device_name)
        print("profile:        ", client.profile_token)
        print("video source:   ", client.video_source_token)
        print("zoom:           ", client.has_zoom)
        print("IR cut filter:  ", client.has_ir)
        print("autofocus:      ", client.has_autofocus)

        if not client.video_source_token:
            print("\nNo video source token - Imaging cannot work.")
            print("The camera returned no VideoSourceConfiguration/SourceToken in its profiles.")

        print("\n=== Current picture settings ===")
        try:
            print(await client.get_imaging_settings())
        except OnvifError as err:
            print("error:", err)

        print("\n=== Events ===")
        try:
            await client.create_pullpoint()
            print("subscription created, waiting 20 seconds for events...")
            print("(move in front of the camera)")
            events = await client.pull_messages("PT20S", 10, 30)
            if events:
                for event in events:
                    print(" ", event)
            else:
                print("  no events arrived")
            await client.unsubscribe()
        except OnvifError as err:
            print("error:", err)

    except OnvifError as err:
        print("Could not connect:", err)
    finally:
        await client.close()


asyncio.run(main())
