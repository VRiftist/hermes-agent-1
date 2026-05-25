# Thunderbolt & USB-C Direct Box-to-Box Connection — Debugging Reference

**Date:** 2026-05-24
**Context:** Attempted direct Mac ↔ Linux physical link via Thunderbolt/USB-C cable for low-latency Hermes agent communication.

## Hardware Inventory

**Mac Mini (LumenHubs-Mini, 192.168.1.240):**
- 4 Thunderbolt/USB4 buses (Bus 0–3), all at "Up to 40 Gb/s"
- 1 built-in Ethernet (en0)
- 4 Thunderbolt adapter ports (en2–en5) feeding into `bridge0`
- Wi-Fi (en1) — active, connected to OpenWrt router

**Linux Box (192.168.1.230, user gerald):**
- Unknown port layout — **must be verified physically**

## What We Tried & What Happened

### Attempt: Thunderbolt cable (or USB-C cable?)

1. Plugged cable into a Mac Thunderbolt port → other end to Linux box
2. `system_profiler SPThunderboltDataType` — **all 4 buses report "No device connected"**
3. Kernel logs detected USB-C activity on `Port-USB-C@1`:
   ```
   IOPortTransportStateUSB3::setActive(): [Port-USB-C@1: USB3] active: YES
   AppleT8112USBXDCI@0: setting USB device address 5, configuration 1
   ```
4. **But no Thunderbolt enumeration anywhere** — zero `IOThunderbolt*` entries showed a connected device

### Root Cause: USB-C != Thunderbolt

The cable being used is almost certainly a **USB-C cable without Thunderbolt certification**. Key evidence:

| Signal | USB-C only | Thunderbolt cable |
|--------|-----------|-------------------|
| Kernel detection | `Port-USB-C@1` traffic visible | `IOThunderbolt*` device enumerated |
| `system_profiler SPThunderboltDataType` | "No device connected" on all buses | Shows device, link speed, vendor |
| `bridge0` status | `status: inactive` | Becomes active with member link |
| `ioreg -p IOThunderboltFamily` | Empty device tree | Shows routed topology |

The Mac's USB-C controllers (`AppleT8112USBXHCI`) saw the plug event and tried to enumerate a USB device, but since the cable doesn't carry Thunderbolt tunneling protocol, the Thunderbolt subsystem never activated. The `bridge0` bridge (members en2–en5) remained inactive because it needs a Thunderbolt link to have a physical member.

### Replug result
Unplugging and replugging produced the same outcome — USB-C detected, Thunderbolt silent. Confirmed: cable capability issue, not a seating problem.

## Diagnostic Commands (Quick Reference)

```bash
# Check Thunderbolt bus status (the definitive test)
system_profiler SPThunderboltDataType

# Check if any Thunderbolt device is in IORegistry
ioreg -p IOThunderboltFamily -l | grep -i "device\|connected\|status"

# Check bridge0 (Thunderbolt Bridge) status
ifconfig bridge0

# Look for USB-C kernel events
log show --predicate 'eventMessage contains "USB" or eventMessage contains "thunder"' --last 5m

# Check what's actually connected to USB
system_profiler SPUSBDataType

# List all network hardware (including Thunderbolt ports)
networksetup -listallhardwareports
```

## Working Alternatives for Low-Latency Direct Link

### Option 1: Ethernet cable (simplest, recommended)
- Cat6 patch cable from Mac en0 (or USB-C-to-Ethernet adapter) → Linux Ethernet port
- Expected latency: **<1ms** round-trip
- No driver issues, no protocol negotiation

### Option 2: Thunderbolt direct (if both boxes have Thunderbolt)
- Requires a **Thunderbolt 3/4 certified cable** (look for ⚡ symbol)
- Both machines must have Thunderbolt ports
- Can create a `bridge0` or `ip` network link over the Thunderbolt interface
- Expected latency: **sub-1ms**

### Option 3: Thunderbolt-to-Ethernet adapter
- If Linux has Ethernet but Mac-side Thunderbolt is available
- Use a Thunderbolt-to-Gigabit-Ethernet adapter on Mac
- Then Cat6 cable to Linux
- Note: adapter must be Thunderbolt-certified, not USB-C

## Key Takeaway

> **USB-C and Thunderbolt cables are NOT interchangeable for networking purposes.** A USB-C cable will show kernel USB activity but will never create a Thunderbolt link, bridge, or network interface. Look for the ⚡ Thunderbolt logo on the cable.