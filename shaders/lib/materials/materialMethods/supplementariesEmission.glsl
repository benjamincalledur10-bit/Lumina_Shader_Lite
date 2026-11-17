#ifndef INCLUDE_SUPPLEMENTARIES_EMISSION
#define INCLUDE_SUPPLEMENTARIES_EMISSION

// Masks for Supplementaries' default textures. State selection belongs in
// block.properties: unlit sconces and powered redstone lanterns never get these IDs.
// Do not recolor textures, force the block lightmap, or make the frame emissive.
float GetSupplementariesEmission(vec3 c, int material) {
    float mask = 0.0;
    float brightness = 0.0;
    float strength = 3.0;
    float whiteCore = smoothstep(0.88, 0.98, min(c.r, min(c.g, c.b)));

    if (material == 10992 || material == 11005) { // Stone/deepslate lamps, warm sconces
        mask = max(smoothstep(0.10, 0.30, c.r - c.b), whiteCore);
        brightness = smoothstep(0.55, 0.85, max(c.r, c.g));
    } else if (material == 10996 || material == 11009) { // Blackstone lamp, soul sconces
        mask = max(smoothstep(0.12, 0.35, max(c.g, c.b) - c.r), whiteCore);
        brightness = smoothstep(0.55, 0.85, max(c.g, c.b));
        if (material == 11009) strength = 2.5;
    } else if (material == 11000) { // Magenta rune; exclude the pale end-stone body
        mask = smoothstep(0.15, 0.45, min(c.r, c.b) - c.g);
        brightness = smoothstep(0.60, 0.90, max(c.r, c.b));
    } else if (material == 11013) { // Green sconces
        mask = max(smoothstep(0.05, 0.20, c.g - max(c.r, c.b)), whiteCore);
        brightness = smoothstep(0.45, 0.85, c.g);
    } else if (material == 11017) { // Redstone lantern, powered=false
        mask = smoothstep(0.12, 0.35, c.r - max(c.g, c.b));
        brightness = smoothstep(0.50, 0.85, c.r);
        strength = 2.5;
    }
    return mask * brightness * strength;
}

#endif
