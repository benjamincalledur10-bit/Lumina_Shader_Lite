#ifndef INCLUDE_SHADOW_PROJECTION
#define INCLUDE_SHADOW_PROJECTION

// The writer and every depth comparison must use the same clip-space transform.
const float shadowDepthScale = 0.3;

vec3 DistortShadowClip(vec3 clipPos) {
    float distortFactor = length(clipPos.xy) * shadowMapBias + (1.0 - shadowMapBias);
    clipPos.xy /= distortFactor;
    clipPos.z *= shadowDepthScale;
    return clipPos;
}

#endif
