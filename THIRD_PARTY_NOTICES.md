# Third-party notices

pymecheye includes the following notices for third-party code compiled into its
native extension. The original texts are distributed under `mecheye/licenses/`.

| Component | License | Notice |
| --- | --- | --- |
| nanobind | BSD 3-Clause | `src/mecheye/licenses/nanobind/LICENSE` |
| robin-map | MIT | `src/mecheye/licenses/robin-map/LICENSE` |
| Mech-Mind SDK header code | BSD 3-Clause header notice | `src/mecheye/licenses/mech-eye/HEADER-NOTICE.txt` |

The Mech-Mind notice preserves the copyright and terms from the SDK 2.6.0
`Camera.h` header. It does not license the proprietary SDK runtime.

Mech-Eye C++ SDK headers, import libraries, and runtime binaries are not bundled.
Users obtain the SDK separately under its vendor agreement and accompanying
licenses. The package's terms do not grant rights to redistribute vendor assets.

NumPy is installed as a separate dependency with its own notices. scikit-build-core
is a build tool whose implementation is not included in the extension. System C++
runtimes and Windows VC++ Redistributable are supplied by the target system.
