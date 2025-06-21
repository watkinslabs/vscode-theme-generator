#!/bin/bash

# Generate 50 cool, stylish, and retro VS Code themes

themes=(
    # Neon/Synthwave vibes
    "neon_cascade:Electric neon waterfall with hot pink and cyan:WL-Neon Cascade"
    "chrome_dreams:Metallic chrome reflections with purple highlights:WL-Chrome Dreams"
    "laser_grid:80s grid landscape with neon lasers:WL-Laser Grid"
    "midnight_drive:Dark highway with neon street lights:WL-Midnight Drive"
    "electric_sunset:Vibrant orange and purple twilight:WL-Electric Sunset"
    "plasma_storm:Electric purple plasma energy:WL-Plasma Storm"
    "cyber_rain:Digital rain in electric blue:WL-Cyber Rain"
    "neon_tokyo:Vibrant city lights at night:WL-Neon Tokyo"
    "synthwave_rider:Hot pink and cyan racing vibes:WL-Synthwave Rider"
    "retro_arcade:Bright cabinet glow aesthetic:WL-Retro Arcade"
    
    # Chill/Relaxed themes
    "cosmic_drift:Soft nebula purples and blues:WL-Cosmic Drift"
    "zen_twilight:Peaceful dusk colors:WL-Zen Twilight"
    "misty_mountain:Soft fog and forest greens:WL-Misty Mountain"
    "velvet_night:Deep purple velvet darkness:WL-Velvet Night"
    "pastel_dream:Soft pastel rainbow:WL-Pastel Dream"
    "aurora_glow:Northern lights soft greens:WL-Aurora Glow"
    "silk_road:Warm desert sand tones:WL-Silk Road"
    "moon_phase:Silvery lunar glow:WL-Moon Phase"
    "jade_temple:Peaceful jade greens:WL-Jade Temple"
    "crystal_cave:Cool crystal blues:WL-Crystal Cave"
    
    # Vibrant/Energetic themes
    "solar_flare:Explosive orange and yellow:WL-Solar Flare"
    "volt_surge:Electric yellow lightning:WL-Volt Surge"
    "prism_break:Rainbow light refraction:WL-Prism Break"
    "acid_wash:Bright psychedelic colors:WL-Acid Wash"
    "pixel_punch:Vibrant pixel art colors:WL-Pixel Punch"
    "turbo_boost:Racing red and white:WL-Turbo Boost"
    "quantum_leap:Bright quantum energy:WL-Quantum Leap"
    "fusion_core:Hot plasma orange:WL-Fusion Core"
    "hyper_drive:Speed blur colors:WL-Hyper Drive"
    "nova_burst:Exploding star colors:WL-Nova Burst"
    
    # Retro tech aesthetic
    "circuit_board:Green PCB traces on black:WL-Circuit Board"
    "vacuum_glow:Warm tube amplifier orange:WL-Vacuum Glow"
    "terminal_green:Classic green phosphor:WL-Terminal Green"
    "amber_monitor:Vintage amber display:WL-Amber Monitor"
    "punch_tape:Retro computing beige:WL-Punch Tape"
    "signal_wave:Oscilloscope green waves:WL-Signal Wave"
    "data_stream:Binary blue and white:WL-Data Stream"
    "mainframe_blue:Corporate computer blue:WL-Mainframe Blue"
    "tape_deck:Cassette brown and silver:WL-Tape Deck"
    "dial_tone:Retro phone colors:WL-Dial Tone"
    
    # Artistic/Stylish themes
    "ink_splash:Bold ink on paper:WL-Ink Splash"
    "graffiti_wall:Street art vibrant spray:WL-Graffiti Wall"
    "lava_lamp:Flowing warm blob colors:WL-Lava Lamp"
    "disco_ball:Sparkly mirror ball reflections:WL-Disco Ball"
    "neon_sign:Glowing sign colors:WL-Neon Sign"
    "chrome_noir:Dark chrome and shadows:WL-Chrome Noir"
    "electric_dreams:Vibrant digital fantasy:WL-Electric Dreams"
    "pulse_wave:Rhythmic color pulses:WL-Pulse Wave"
    "cyber_punk:Dark with neon accents:WL-Cyber Punk"
    "retro_future:Yesterday's tomorrow aesthetic:WL-Retro Future"
)

# Loop through and generate each theme
for theme_data in "${themes[@]}"; do
    # Split the theme data into name, description, and display name
    IFS=':' read -r theme_name theme_desc display_name <<< "$theme_data"
    
    echo "Generating theme: ${display_name}"
    python -m vscode_theme_generator quickstart "${theme_name}" "${theme_desc}" --from-prompt "${theme_desc}" --display-name "${display_name}"
    
    # Small delay to avoid overwhelming the system
    sleep 0.5
done

echo "Successfully generated 50 retro themes!"