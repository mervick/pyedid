# VESA EDID https://en.wikipedia.org/wiki/Extended_Display_Identification_Data
# VESA EDID https://glenwing.github.io/docs/VESA-EEDID-A1.pdf
# VESA DMT https://glenwing.github.io/docs/VESA-DMT-1.13.pdf


import re
from pyedid.pnp_id_list import registry


def hex2int(hex_str):
    return int("0x" + hex_str, 16)


class InvalidEdidException(Exception):
    pass


class EDID:
    def __init__(self, hex):
        hex = re.sub(r"\s+", "", hex)
        self.data = {}
        self.bytes = []
        for i in range(0, int(len(hex) / 2)):
            self.bytes.append(hex[i*2:i*2+2])

    def hex(self, num, count=1, reverse=False):
        hex_arr = []
        for i in range(num, num + count):
            hex_arr.append(self.bytes[i])
        return "".join(hex_arr if not reverse else list(reversed(hex_arr)))

    def byte(self, num, count=1, reverse=False):
        return hex2int(self.hex(num, count, reverse))

    def chars(self, num, count=1, terminate_nl=False):
        chars = []
        for i in range(num, num + count):
            byte = self.byte(i)
            if terminate_nl and byte in (0x0a, 0x00):
                break
            chars.append(chr(byte))
        return "".join(chars)

    @staticmethod
    def combine(binary, dict_stack, keys=None, additional=None):
        bin_key = keys["bin"] if keys and "bin" in keys else "bin"
        txt_key = keys["value"] if keys and "value" in keys else "value"
        txt = dict_stack[binary] if binary in dict_stack else None
        dict_ret = {
            bin_key: binary,
            txt_key: txt
        }
        if additional is not None and type(additional) == dict:
            dict_ret.update(additional)
        return dict_ret

    def parse(self):
        # EDID Format fixed header pattern
        if self.hex(0, 8).lower() != "00ffffffffffff00":
            raise InvalidEdidException("Invalid EDID format")

        # ID Manufacturer Name, EISA 3-character ID
        byte = self.byte(8, 2)
        chars = [(byte >> 10) & 0b11111, (byte >> 5) & 0b11111, byte & 0b11111]
        for i, val in enumerate(chars):
            chars[i] = chr(val + 64)
        manufacturer_id = "".join(chars)
        self.data["manufacturer_id"] = manufacturer_id

        if manufacturer_id in registry:
            self.data["manufacturer_name"] = registry[manufacturer_id]

        # ID Product Code
        product_code = self.byte(0x0a, 2, True)
        self.data["product_code"] = product_code

        # ID Serial Number
        serial_number = self.byte(0x0c, 4, True)
        self.data["serial_number"] = serial_number

        # EDID Structure Version / Revision
        self.data["edid_version"] = edid_version = self.byte(0x12)
        self.data["edid_revision"] = edid_revision = self.byte(0x13)

        # Week of Manufacture
        week_of_manufacture = self.byte(0x10)
        self.data["week_of_manufacture"] = week_of_manufacture

        # Year of Manufacture
        year_of_manufacture = self.byte(0x11) + 1990
        self.data["year_of_manufacture"] = year_of_manufacture

        # Basic Display Parameters / Features

        # Video Input Definition
        video_input = self.byte(0x14)
        digital = video_input >> 7 & 1

        if digital:  # Digital input
            self.data["signal_type"] = "digital"

            # Bit depth
            depth = video_input >> 4 & 0b111
            depths = {
                0b001: 6,
                0b010: 8,
                0b011: 10,
                0b100: 12,
                0b110: 16,
            }
            self.data["digital_depth"] = self.combine(depth, depths)

            # Video interface
            interface = video_input & 0b1111
            interfaces = {
                0b010: "HDMIa",
                0b011: "HDMIb",
                0b100: "MDDI",
                0b101: "DisplayPort",
            }
            self.data["digital_interface"] = self.combine(interface, interfaces)
            # DFP 1.x. If set = 1, Interface is signal compatible with VESA DFP 1.x
            # TMDS CRGB, 1 pixel / clock, up to 8 bits / color MSB aligned, DE active high
            self.data["digital_dfp1"] = 1 if video_input & 0b1111111 == 1 else 0

        else:  # Analog input
            self.data["signal_type"] = "analog"

            # Signal Level Standard
            signal_standard = video_input >> 5 & 0b11
            #  Format is "reference white above blank", "level of sync. tip below blank", "volts (V p-p)"
            signal_standards = {
                0b00: [0.700, 0.300, 1.000],
                0b01: [0.714, 0.286, 1.000],
                0b10: [1.000, 0.400, 1.400],
                0b11: [0.700, 0.000, 0.700],
            }
            self.data["analog_signal_standard"] = self.combine(signal_standard, signal_standards)
            support = []
            for shift in reversed(range(0, 5)):
                support.append(video_input >> shift & 1)

            # Setup, If set = 1, the display expects a blank-to-black setup or pedestal per
            # appropriate Signal Level Standard
            self.data["analog_setup"] = support[0]
            self.data["analog_support_separate_sync"] = support[1]    # If 1, separate syncs. supported
            self.data["analog_support_composite_sync"] = support[2]   # If 1, composite sync. (on Hsync line) supported
            self.data["analog_support_sync_on_green"] = support[3]    # If 1, sync. on green video supported
            # If 1, serration of the Vsync. Pulse is required when composite sync. or sync-on-green video is used
            self.data["analog_support_vsync_serration"] = support[4]

        # Horizontal screen size, in centimetres (range 1–255). If vertical screen size is 0,
        # landscape aspect ratio (range 1.00–3.54), datavalue = (AR×100) − 99 (example: 16:9, 79; 4:3, 34.)
        self.data["h_size"] = self.byte(0x15)  # Max. Horizontal Image Size (cm)

        # Vertical screen size, in centimetres. If horizontal screen size is 0,
        # portrait aspect ratio (range 0.28–0.99), datavalue = (100/AR) − 99 (example: 9:16, 79; 3:4, 34.)
        # If both bytes are 0, screen size and aspect ratio are undefined (e.g. projector)
        self.data["v_size"] = self.byte(0x16)   # Max. Vertical Image Size (cm)

        # Display gamma, factory default (range 1.00–3.54), datavalue = (gamma×100) − 100 = (gamma − 1)×100.
        # If 255, gamma is defined by DI-EXT block.
        self.data["gamma"] = self.byte(0x17)

        # Feature Support
        feature = self.byte(0x18)

        # Standby VESA DPMS supported
        self.data["feature_standby"] = feature >> 7 & 1

        # Suspend VESA DPMS supported
        self.data["feature_suspend"] = feature >> 6 & 1

        # Active Off/Very Low Power
        # The display consumes much less power when it receives a timing signal that is outside its declared active
        # operating range. The display will revert to normal operation if the timing signal returns to the normal
        # operating range. No sync. signals is one example of a timing signal outside normal operating range.
        # No DE signal is another example
        self.data["feature_active_off"] = feature >> 5 & 1

        # Display Type
        display_type = feature >> 3 & 0b11
        if digital:
            display_types = {
                0b00: "RGB 4:4:4",
                0b01: "RGB 4:4:4 + YCrCb 4:4:4",
                0b10: "RGB 4:4:4 + YCrCb 4:2:2",
                0b11: "RGB 4:4:4 + YCrCb 4:4:4 + YCrCb 4:2:2",
            }
        else:
            display_types = {
                0b00: "Monochrome / grayscale display",
                0b01: "RGB color display",
                0b10: "Non-RGB multicolor display",
                0b11: "Undefined",
            }
        self.data["display_type"] = display_types[display_type]
        self.data["display_type_bin"] = display_type

        # Standard Default Color Space, sRGB
        # If this bit is set to 1, the display uses the sRGB standard default color space as its primary color space.
        # If this bit is set, the color information must match the sRGB standard values.
        self.data["feature_srgb"] = sRGB = feature >> 2 & 1

        # Preferred Timing Mode
        # If this bit is set to 1, the display’s preferred timing mode is indicated in the first detailed timing block.
        # Note: Use of preferred timing mode is required by EDID Structure Version 1 Revision 3 and higher
        self.data["feature_preferred_timing_mode"] = feature >> 1 & 1

        # Default GTF supported
        # If this bit is set to 1, the display supports timings based on the GTF
        # standard using default GTF parameter values
        self.data["feature_default_gtf"] = is_gtf = feature & 1

        # Color Characteristics
        self.data["colors"] = {}
        self.data["colors"]["red_green_low_bits_bin"] = self.byte(0x19)  # Red/Green Low Bits
        self.data["colors"]["blue_white_low_bits_bin"] = self.byte(0x1a)  # Blue/White Low Bits
        self.data["colors"]["red_x_bin"] = self.byte(0x1b)  # Red-x
        self.data["colors"]["red_y_bin"] = self.byte(0x1c)  # Red-y
        self.data["colors"]["green_x_bin"] = self.byte(0x1d)  # Green-x
        self.data["colors"]["green_y_bin"] = self.byte(0x1e)  # Green-y
        self.data["colors"]["blue_x_bin"] = self.byte(0x1f)  # Blue-x
        self.data["colors"]["blue_y_bin"] = self.byte(0x20)  # Blue-y
        self.data["colors"]["white_x_bin"] = self.byte(0x21)  # White-x
        self.data["colors"]["white_y_bin"] = self.byte(0x22)  # White-y

        # Established Timings
        # self.data["established_timings1_bin"] = timings1 = self.byte(0x23)
        # self.data["established_timings2_bin"] = timings2 = self.byte(0x24)
        # self.data["manufacturers_timings_bin"] = timings3 = self.byte(0x25)
        timings1 = self.byte(0x23)
        timings2 = self.byte(0x24)
        timings3 = self.byte(0x25)
        timings = []

        for shift, timing in enumerate([
            "800x600 @ 60Hz",
            "800x600 @ 56Hz",
            "640x480 @ 75Hz",
            "640x480 @ 72Hz",
            "640x480 @ 67Hz",
            "640x480 @ 60Hz",
            "720x400 @ 88Hz",
            "720x400 @ 70Hz",
        ]):
            if timings1 >> shift & 1:
                timings.append(timing)

        for shift, timing in enumerate([
            "1280x1024 @ 75Hz",
            "1024x768 @ 75Hz",
            "1024x768 @ 70Hz",
            "1024x768 @ 60Hz",
            "1024x768i @ 87Hz",
            "832x624 @ 75Hz",
            "800x600 @ 75Hz",
            "800x600 @ 72Hz",
        ]):
            if timings2 >> shift & 1:
                timings.append(timing)

        if timings3 >> 7 & 1:
            timings.append("1152 x 870 @ 75Hz")

        self.data["established_timings"] = timings

        # Standard Timing Identification
        ratios = {
            # EDID structures prior to Version 1.3 defined the bit combination of 0b00 to indicate a 1:1 aspect ratio
            0b00: "16:10" if (edid_version == 1 and edid_revision >= 3) or edid_version > 1 else "1:1",
            0b01: "4:3",
            0b10: "5:4",
            0b11: "16:9",
        }

        timings = []
        for i in range(0, 8):  # 0x26 - 0x36
            timing = self.byte(0x26 + i * 2, 2)
            if timing == 0x0101:  # Unused field
                continue
            # The range of horizontal active pixels that can be described in each byte is 256 → 2288 pixels,
            # in increments of 8 pixels. (Horizontal active pixels / 8) - 31
            h_pixels = ((timing >> 8 & 0xff) + 31) * 8
            # The vertical active line count may be calculated from the aspect ratio and the Horizontal active pixel
            # count given in the first byte. “Square” pixels (1:1 pixel aspect ratio) shall be assumed.
            ratio = ratios[timing >> 6 & 0b11].split(":")
            v_pixels = h_pixels / int(ratio[0]) * int(ratio[1])
            # Refresh rate, Range 60 - 123Hz
            rate = (timing & 0b111111) + 60
            timings.append("%dx%d @ %dHz" % (h_pixels, v_pixels, rate))

        self.data["standard_timings"] = timings

        # Detailed Timing Descriptions or Monitor Descriptors
        timings = []
        detailed_timings = []
        descriptors = []

        descriptor_ascii_types = {
            0xfc: "Monitor name",
            0xfe: "ASCII text",
            0xff: "Monitor serial number",
        }
        descriptor_types = {
            0xfd: "Display range limits",
            0xfb: "Additional white point data",
            0xfa: "Additional standard timing identifiers",
            0xf9: "Display Color Management",
            0xf8: "CVT 3-Byte Timing Codes",
            0xf7: "Additional standard timing 3",
            0x10: "Dummy identifier"
        }

        for i in (0x36, 0x48, 0x5a, 0x6c):
            descriptor = self.byte(i, 5)
            if descriptor & 0xfffffff000 == 0xf000 or descriptor & 0xffffffffff == 0x1000:
                descriptor_type = descriptor >> 8
                descriptor_reserved = descriptor & 0xff

                # Display Range Limits Descriptor
                if descriptor_type == 0xfd:
                    if descriptor_reserved >> 4 & 0xf == 0:
                        # Offsets for display range limits
                        # rate_offsets = {
                        #     0b10: "+255 kHz for max. rate",
                        #     0b11: "+255 kHz for max. and min. rates",
                        # }
                        # Horizontal rate offsets:
                        h_rate_offset = descriptor_reserved >> 2 & 0b11
                        # h_rate_offset = self.combine(h_rate_offset, rate_offsets)
                        # Vertical rate offsets:
                        v_rate_offset = descriptor_reserved & 0b11
                        # v_rate_offset = self.combine(v_rate_offset, rate_offsets)
                        min_v_rate = self.byte(i + 5) + (0xff if v_rate_offset == 0b11 else 0)
                        max_v_rate = self.byte(i + 6) + (0xff if v_rate_offset == 0b10 else 0)
                        min_h_rate = self.byte(i + 7) + (0xff if h_rate_offset == 0b11 else 0)
                        max_h_rate = self.byte(i + 8) + (0xff if h_rate_offset == 0b10 else 0)
                        # Maximum pixel clock rate, rounded up to 10 MHz multiple (10–2550 MHz).
                        max_pixel_clock = self.byte(i + 9) * 10000
                        # Extended timing information type
                        extended_type = self.byte(i + 10)
                        extended_types = {
                            0x00: "Default GTF",
                            0x01: "No timing information",
                            0x02: "Secondary GTF supported",
                            0x04: "CVT",
                        }
                        extended_type_dict = self.combine(extended_type, extended_types)

                        self.data["range_limits"] = {
                            "min_v_rate": min_v_rate,
                            "max_v_rate": max_v_rate,
                            "min_h_rate": min_h_rate,
                            "max_h_rate": max_h_rate,
                            "max_pixel_clock": max_pixel_clock,
                            "extended_type": extended_type_dict,
                            "timings": self.hex(i + 11, 7)
                        }

                # Monitor Descriptor
                elif descriptor_reserved == 0:
                    if descriptor_type in descriptor_ascii_types.keys():
                        text = self.chars(i + 5, 13, True)
                        descriptors.append(self.combine(descriptor_type, descriptor_ascii_types,
                                                        {"bin": "type", "value": "desc"}, {
                                                            "text": text,
                                                        }))
                    elif descriptor_type in descriptor_types.keys():
                        hex = self.hex(i + 5, 13)
                        descriptors.append(self.combine(descriptor_type, descriptor_types,
                                                        {"bin": "type", "value": "desc"}, {
                                                            "hex": hex,
                                                        }))

            else:  # Detailed Timing Description
                # Pixel clock in 10 kHz units (0.01–655.35 MHz, little-endian)
                pixel_clock = self.byte(i, 2, True) * 10000
                if not pixel_clock:
                    continue

                # Horizontal active pixels 8 lsbits
                h_active = self.byte(i + 2)
                # Horizontal blanking pixels 8 lsbits
                h_blanking = self.byte(i + 3)
                msbits = self.byte(i + 4)
                # Horizontal active pixels 4 msbits
                h_active |= (msbits >> 4 & 0x0f) << 8
                # Horizontal blanking pixels 4 msbits
                h_blanking |= (msbits & 0x0f) << 8

                # Vertical active lines 8 lsbits
                v_active = self.byte(i + 5)
                # Vertical blanking lines 8 lsbits
                v_blanking = self.byte(i + 6)
                msbits = self.byte(i + 7)
                # Vertical active lines 4 msbits
                v_active |= (msbits >> 4 & 0x0f) << 8
                # Vertical blanking lines 4 msbits
                v_blanking |= (msbits & 0x0f) << 8

                # Horizontal front porch (sync offset) pixels 8 lsbits
                h_front_porch = self.byte(i + 8)
                # Horizontal sync pulse width pixels 8 lsbits
                h_pulse_width = self.byte(i + 9)
                lsbits = self.byte(i + 10)
                # Vertical front porch (sync offset) lines 4 lsbits
                v_front_porch = lsbits >> 4 & 0x0f
                # Vertical sync pulse width lines 4 lsbits
                v_pulse_width = lsbits & 0x0f

                msbits = self.byte(i + 11)
                # Horizontal front porch (sync offset) pixels 2 msbits
                h_front_porch |= (msbits >> 6 & 0b11) << 8
                # Horizontal sync pulse width pixels 2 msbits
                h_pulse_width |= (msbits >> 4 & 0b11) << 8
                # Vertical front porch (sync offset) lines 2 msbits
                v_front_porch |= (msbits >> 2 & 0b11) << 4
                # Vertical sync pulse width lines 2 msbits
                v_pulse_width |= (msbits & 0b11) << 4

                # Horizontal image size, mm, 8 lsbits (0–255 mm)
                h_image_size = self.byte(i + 12)
                # Vertical image size, mm, 8 lsbits (0–255 mm)
                v_image_size = self.byte(i + 13)
                msbits = self.byte(i + 14)
                # Horizontal image size, mm, 4 msbits
                h_image_size |= (msbits >> 4 & 0x0f) << 8
                # Vertical image size, mm, 4 msbits
                v_image_size |= (msbits & 0x0f) << 8

                h_border = self.byte(i + 15)
                v_border = self.byte(i + 16)

                # Features bitmap
                features = self.byte(i + 17)

                # Signal Interface Type
                interlaced = features >> 7 & 1
                signal_types = {
                    0: "non-interlaced",
                    1: "interlaced"
                }
                interlaced = self.combine(interlaced, signal_types)

                # Stereo mode
                modes = {
                    0b010: "field sequential, right during stereo sync",
                    0b100: "field sequential, left during stereo sync",
                    0b011: "2-way interleaved, right image on even lines",
                    0b101: "2-way interleaved, left image on even lines",
                    0b110: "4-way interleaved",
                    0b111: "side-by-side interleaved",
                }
                mode = (features >> 4 & 0b110) | (features & 1)
                mode = self.combine(mode, modes)

                sync = {"signal": None}
                analog_sync = features >> 4 & 1

                # Analog sync.
                if analog_sync:
                    sync["signal"] = "analog"
                    sync["type"] = self.combine(features >> 3 & 1, {
                        0: "analog composite",
                        1: "bipolar analog composite"
                    })
                    sync["serration"] = self.combine(features >> 2 & 1, {
                        0: "without serrations",
                        1: "with serrations (H-sync during V-sync)"
                    })
                    # Sync on red and blue lines additionally to green
                    sync["rgb"] = self.combine(features >> 1 & 1, {
                        0: "sync on green signal only",
                        1: "sync on all three (RGB) video signals"
                    })
                else:
                    digital_sync = features >> 3 & 0b11

                    # Digital sync., composite (on HSync)
                    if digital_sync == 0b10:
                        sync["signal"] = "digital"
                        sync["type"] = "digital composite"
                        sync["serration"] = self.combine(features >> 2 & 1, {
                            0: "without serrations",
                            1: "with serrations (H-sync during V-sync)"
                        })
                        # Horizontal sync polarity
                        sync["polarity"] = self.combine(features >> 1 & 1, {
                            0: "negative",
                            1: "positive"
                        })

                    # Digital sync., separate
                    elif digital_sync == 0b11:
                        sync["signal"] = "digital"
                        sync["type"] = "digital separate"
                        # Vertical sync polarity
                        sync["polarity"] = self.combine(features >> 2 & 1, {
                            0: "negative",
                            1: "positive"
                        })
                        # Horizontal sync polarity
                        sync["polarity"] = self.combine(features >> 1 & 1, {
                            0: "negative",
                            1: "positive"
                        })
                # blanking = front porch + sync width + back porch
                # pixel_clock = (h_blanking + h_active) * (v_blanking + v_active) * frame_rate
                frame_rate = round(pixel_clock / ((h_blanking + h_active) * (v_blanking + v_active)))

                detailed_timings.append({
                    "pixel_clock": pixel_clock,
                    "frame_rate": frame_rate,
                    "h_active": h_active,
                    "h_blanking": h_blanking,
                    "v_active": v_active,
                    "v_blanking": v_blanking,
                    "h_front_porch": h_front_porch,
                    "h_pulse_width": h_pulse_width,
                    "v_front_porch": v_front_porch,
                    "v_pulse_width": v_pulse_width,
                    "h_image_size": h_image_size,
                    "v_image_size": v_image_size,
                    "h_border": h_border,
                    "v_border": v_border,
                    "interlaced": interlaced,
                    "stereo_mode": mode,
                    "sync": sync,
                })
                timings.append("%dx%d%s @ %dHz" % (h_active, v_active, 'i' if interlaced["bin"] else '', frame_rate))

        self.data["detailed_timings"] = detailed_timings
        self.data["descriptors"] = descriptors
        self.data["timings"] = timings + self.data["standard_timings"] + self.data["established_timings"]

        return self.data
