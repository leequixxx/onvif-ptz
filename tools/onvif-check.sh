#!/bin/sh
# Quick ONVIF check over curl.
#
#   sh onvif-check.sh 192.168.2.2 80 admin PASSWORD
#
# The timestamp is taken from the camera's own clock (GetSystemDateAndTime
# needs no authentication), so clock drift does not interfere.

HOST="${1:?host required}"; PORT="${2:-80}"; USER="${3:?username required}"; PASS="${4:?password required}"
DEV="http://$HOST:$PORT/onvif/device_service"
MEDIA="http://$HOST:$PORT/onvif/media_service"
IMG="http://$HOST:$PORT/onvif/imaging_service"
DEV_EVENTS="http://$HOST:$PORT/onvif/event_service"
CT='Content-Type: application/soap+xml; charset=utf-8'

# --- WSSE UsernameToken ---
# The nonce must be unique for EVERY request: cameras implement replay
# protection and answer NotAuthorized to a second request carrying the
# same value. The header is therefore rebuilt before each call.
wsse() {
  NONCE_FILE=$(mktemp)
  openssl rand 16 > "$NONCE_FILE"
  NONCE_B64=$(openssl base64 -A -in "$NONCE_FILE")
  DIGEST=$( { cat "$NONCE_FILE"; printf '%s%s' "$CREATED" "$PASS"; } \
            | openssl dgst -sha1 -binary | openssl base64 -A )
  rm -f "$NONCE_FILE"

  printf '%s' "<s:Header><Security s:mustUnderstand=\"1\"
    xmlns=\"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-secext-1.0.xsd\">
    <UsernameToken><Username>$USER</Username>
    <Password Type=\"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-username-token-profile-1.0#PasswordDigest\">$DIGEST</Password>
    <Nonce EncodingType=\"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-soap-message-security-1.0#Base64Binary\">$NONCE_B64</Nonce>
    <Created xmlns=\"http://docs.oasis-open.org/wss/2004/01/oasis-200401-wss-wssecurity-utility-1.0.xsd\">$CREATED</Created>
    </UsernameToken></Security></s:Header>"
}

soap() { # url body [auth]
  HDR=""
  [ -n "$3" ] && HDR=$(wsse)
  printf '%s' "<?xml version=\"1.0\"?><s:Envelope
    xmlns:s=\"http://www.w3.org/2003/05/soap-envelope\"
    xmlns:tds=\"http://www.onvif.org/ver10/device/wsdl\"
    xmlns:trt=\"http://www.onvif.org/ver10/media/wsdl\"
    xmlns:timg=\"http://www.onvif.org/ver20/imaging/wsdl\"
    xmlns:tev=\"http://www.onvif.org/ver10/events/wsdl\"
    xmlns:wsa=\"http://www.w3.org/2005/08/addressing\"
    xmlns:tt=\"http://www.onvif.org/ver10/schema\">$HDR<s:Body>$2</s:Body></s:Envelope>" \
  | curl -s -m 15 -X POST "$1" -H "$CT" --data-binary @-
}

# --- camera clock: without it WSSE fails once the clock has drifted ---
TIME_XML=$(soap "$DEV" "<tds:GetSystemDateAndTime/>")
get() { printf '%s' "$TIME_XML" | sed -n "s/.*<tt:$1>\([0-9]*\)<\/tt:$1>.*/\1/p" | head -1; }
Y=$(get Year); MO=$(get Month); D=$(get Day)
H=$(get Hour); MI=$(get Minute); SE=$(get Second)

if [ -n "$Y" ]; then
  CREATED=$(printf '%04d-%02d-%02dT%02d:%02d:%02dZ' "$Y" "$MO" "$D" "$H" "$MI" "$SE")
  echo "Camera clock: $CREATED   (now: $(date -u +%Y-%m-%dT%H:%M:%SZ))"
else
  CREATED=$(date -u +%Y-%m-%dT%H:%M:%SZ)
  echo "Camera reported no time, using ours: $CREATED"
fi

echo
echo "=== GetCapabilities (actual service addresses) ==="
CAP=$(soap "$DEV" "<tds:GetCapabilities><tds:Category>All</tds:Category></tds:GetCapabilities>" auth)
printf '%s' "$CAP" | tr '<' '\n<' | grep -i 'XAddr\|Fault\|Text' | sed 's/^/  /' | head -20

# A greedy pattern across the whole document grabbed the last XAddr in
# sequence. Look the service address up by its endpoint name instead.
IMG_REAL=$(printf '%s' "$CAP" | tr '<' '\n<' \
  | sed -n 's/.*XAddr>\(http[^<]*imaging[^<]*\).*/\1/p' | head -1)
[ -n "$IMG_REAL" ] && IMG="$IMG_REAL"
echo "  -> using Imaging: $IMG"

echo
echo "=== GetVideoSources (source token needed) ==="
VS=$(soap "$MEDIA" "<trt:GetVideoSources/>" auth)
printf '%s\n' "$VS" | tr '>' '>\n' | grep -i 'token\|Fault\|Text' | head -10
TOKEN=$(printf '%s' "$VS" | sed -n 's/.*token="\([^"]*\)".*/\1/p' | head -1)
[ -z "$TOKEN" ] && TOKEN=$(printf '%s' "$VS" | sed -n 's/.*<tt:SourceToken>\([^<]*\)<.*/\1/p' | head -1)
echo "Source token: ${TOKEN:-NOT FOUND}"

[ -z "$TOKEN" ] && { echo; echo "Imaging cannot be checked without a token."; exit 1; }

# Show the filtered output, and the raw reply when nothing matched:
# silence from grep explains nothing on its own.
show() { # heading filter reply
  echo
  echo "=== $1 ==="
  OUT=$(printf '%s' "$3" | tr '>' '>\n' | grep -i "$2" | head -20)
  if [ -n "$OUT" ]; then
    printf '%s\n' "$OUT"
  else
    echo "--- filter matched nothing, raw reply: ---"
    printf '%s\n' "$3" | head -c 900
    echo
  fi
}

R=$(soap "$IMG" "<timg:GetOptions><timg:VideoSourceToken>$TOKEN</timg:VideoSourceToken></timg:GetOptions>" auth)
show "GetOptions (what the camera allows changing)" 'IrCutFilter\|AutoFocus\|Fault\|Text' "$R"

R=$(soap "$IMG" "<timg:GetImagingSettings><timg:VideoSourceToken>$TOKEN</timg:VideoSourceToken></timg:GetImagingSettings>" auth)
show "GetImagingSettings (current values)" 'IrCutFilter\|AutoFocus\|Focus\|Fault\|Text' "$R"

echo
echo "=== Events (motion detection) ==="
SUB=$(soap "$DEV_EVENTS" "<tev:CreatePullPointSubscription><tev:InitialTerminationTime>PT60S</tev:InitialTerminationTime></tev:CreatePullPointSubscription>" auth)
printf '%s' "$SUB" | tr '>' '>\n' | grep -i 'Address\|Fault\|Text' | head -6
# The namespace prefix can be anything (wsa:, wsa5:, a:). The [a-z0-9]
# class after "<" rules out the closing tag: otherwise a greedy .*
# reaches </...:Address> and captures an empty string.
PP=$(printf '%s' "$SUB" | sed -n 's/.*<[a-zA-Z0-9]*:Address>\([^<]*\)<.*/\1/p' | head -1)
if [ -n "$PP" ]; then
  echo "Pull point: $PP"
  echo "Waiting 20 seconds for events - move in front of the camera..."
  soap "$PP" "<tev:PullMessages><tev:Timeout>PT20S</tev:Timeout><tev:MessageLimit>10</tev:MessageLimit></tev:PullMessages>" auth \
    | tr '>' '>\n' | grep -i 'Topic\|SimpleItem\|Fault\|Text' | head -20
else
  echo "Subscription failed - no ONVIF motion detection available."
fi

echo
echo "--- How to read this ---"
echo "NotAuthorized everywhere   -> wrong password, or the user lacks rights."
echo "Empty but no Fault         -> the camera does not implement the method."
echo "IrCutFilter present        -> the night mode switch should appear."
echo "SimpleItem with motion     -> motion detection works."
