# PyEdid

Python Extended Display Identification Data (EDID) metadata parser.

Extended Display Identification Data (EDID) is the metadata format for display devices to describe their capabilities to a video source (e.g. graphics card or set-top box). The data format is defined by a standard published by the Video Electronics Standards Association (VESA).

The EDID data structure includes manufacturer name and serial number, product type, phosphor or filter type (as chromaticity data), timings supported by the display, display size, luminance data and (for digital displays only) pixel mapping data.

DisplayID is a VESA standard targeted to replace EDID and E-EDID extensions with a uniform format suited for both PC monitor and consumer electronics devices.

### Usage
```py
from pyedid import EDID

# edid data of my Lenovo Display
edid_txt = """         
00ffffffffffff0030aeee6548505836
0d1e0103803c22783a4455a9554d9d26
0f5054a1080081809500a9c0b300d1c0
01010101010164e7006aa0a067501520
350055502100001a70c200a0a0a05550
3020350055502100001a000000fd0030
901edf3c000a202020202020000000fc
004c454e20593237712d32300a2001ea
020344f14c61601f9014010304121305
022309070783010000e200d567030c00
1000383c67d85dc401788007681a0000
0101309000e305c000e30f0300e60607
0161561c565e00a0a0a0295030203500
55502100001ea073006aa0a029500820
350055502100001a70a000a0a0a04650
3020350055502100001e000000000073
"""

edid = EDID(edid_txt)
edid.parse()
print(edid.data)

# output
{'colors': {'blue_white_low_bits_bin': 85, 'blue_x_bin': 38, 'blue_y_bin': 15,
            'green_x_bin': 77, 'green_y_bin': 157,
            'red_green_low_bits_bin': 68, 'red_x_bin': 169, 'red_y_bin': 85,
            'white_x_bin': 80, 'white_y_bin': 84},
 'descriptors': [{'desc': 'Monitor name', 'text': 'LEN Y27q-20', 'type': 252}],
 'detailed_timings': [{'frame_rate': 144,
                       'h_active': 2560,
                       'h_blanking': 106,
                       'h_border': 0,
                       'h_front_porch': 21,
                       'h_image_size': 597,
                       'h_pulse_width': 32,
                       'interlaced': {'bin': 0, 'value': 'non-interlaced'},
                       'pixel_clock': 592360000,
                       'stereo_mode': {'bin': 0, 'value': None},
                       'sync': {'rgb': {'bin': 1, 'value': 'sync on all three (RGB) video signals'},
                                'serration': {'bin': 0, 'value': 'without serrations'},
                                'signal': 'analog',
                                'type': {'bin': 1, 'value': 'bipolar analog composite'}},
                       'v_active': 1440,
                       'v_blanking': 103,
                       'v_border': 0,
                       'v_front_porch': 3,
                       'v_image_size': 336,
                       'v_pulse_width': 5},
                      {'frame_rate': 120,
                       'h_active': 2560,
                       'h_blanking': 160,
                       'h_border': 0,
                       'h_front_porch': 48,
                       'h_image_size': 597,
                       'h_pulse_width': 32,
                       'interlaced': {'bin': 0, 'value': 'non-interlaced'},
                       'pixel_clock': 497760000,
                       'stereo_mode': {'bin': 0, 'value': None},
                       'sync': {'rgb': {'bin': 1, 'value': 'sync on all three (RGB) video signals'},
                                'serration': {'bin': 0, 'value': 'without serrations'},
                                'signal': 'analog',
                                'type': {'bin': 1, 'value': 'bipolar analog composite'}},
                       'v_active': 1440,
                       'v_blanking': 85,
                       'v_border': 0,
                       'v_front_porch': 3,
                       'v_image_size': 336,
                       'v_pulse_width': 5}],
 'digital_depth': {'bin': 0, 'value': None},
 'digital_dfp1': 0,
 'digital_interface': {'bin': 0, 'value': None},
 'display_type': 'RGB 4:4:4 + YCrCb 4:4:4 + YCrCb 4:2:2',
 'display_type_bin': 3,
 'edid_revision': 3,
 'edid_version': 1,
 'established_timings': ['800x600 @ 60Hz', '640x480 @ 60Hz', '720x400 @ 70Hz', '1024x768 @ 60Hz'],
 'feature_active_off': 1,
 'feature_default_gtf': 0,
 'feature_preferred_timing_mode': 1,
 'feature_srgb': 0,
 'feature_standby': 0,
 'feature_suspend': 0,
 'gamma': 120,
 'h_size': 60,
 'manufacturer_id': 'LEN',
 'manufacturer_name': 'Lenovo Group Limited',
 'product_code': 26094,
 'range_limits': {'extended_type': {'bin': 0, 'value': 'Default GTF'},
                  'max_h_rate': 223,
                  'max_pixel_clock': 600000,
                  'max_v_rate': 144,
                  'min_h_rate': 30,
                  'min_v_rate': 48,
                  'timings': '0a202020202020'},
 'serial_number': 911757384,
 'signal_type': 'digital',
 'standard_timings': ['1280x1024 @ 60Hz', '1440x900 @ 60Hz', '1600x900 @ 60Hz', '1680x1050 @ 60Hz', '1920x1080 @ 60Hz'],
 'timings': ['2560x1440 @ 144Hz', '2560x1440 @ 120Hz', '1280x1024 @ 60Hz',
             '1440x900 @ 60Hz', '1600x900 @ 60Hz', '1680x1050 @ 60Hz',
             '1920x1080 @ 60Hz', '800x600 @ 60Hz', '640x480 @ 60Hz',
             '720x400 @ 70Hz', '1024x768 @ 60Hz'],
 'v_size': 34,
 'week_of_manufacture': 13,
 'year_of_manufacture': 2020}
```


## Links

[EDID wikipedia](https://en.wikipedia.org/wiki/Extended_Display_Identification_Data)  
[VESA-EEDID format](https://glenwing.github.io/docs/VESA-EEDID-A1.pdf)  
