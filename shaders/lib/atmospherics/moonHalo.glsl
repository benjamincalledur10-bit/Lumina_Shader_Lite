vec3 GetMoonHalo(float VdotS) {
    float moonAlignment = clamp01(-VdotS);
    float haloShape = pow2(smoothstep(0.91, 0.998, moonAlignment));

    float phaseDistance = min(float(moonPhase), 8.0 - float(moonPhase));
    float phaseVisibility = 1.0 - 0.82 * smoothstep(0.0, 4.0, phaseDistance);
    float weatherVisibility = 1.0 - 0.72 * rainFactor;
    float horizonVisibility = GetHorizonFactor(-SdotU);

    float halo = haloShape * phaseVisibility * weatherVisibility * horizonVisibility;
    vec3 haloColor = mix(vec3(0.20, 0.28, 0.46), vec3(0.42, 0.48, 0.62), moonAlignment);
    return haloColor * halo * (0.01 * MOON_HALO_I);
}
