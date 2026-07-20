#include "/lib/colors/skyColors.glsl"

float GetStarNoise(vec2 pos) {
    return fract(sin(dot(pos, vec2(12.9898, 4.1414))) * 43758.54953);
}

vec2 GetStarCoord(vec3 viewPos, float sphereness) {
    vec3 wpos = normalize((gbufferModelViewInverse * vec4(viewPos * 1000.0, 1.0)).xyz);
    vec3 starCoord = wpos / (wpos.y + length(wpos.xz) * sphereness);
    starCoord.x += 0.006 * syncedTime;
    return starCoord.xz;
}

vec3 GetStars(vec2 starCoord, float VdotU, float VdotS) {
    #if NIGHT_STAR_AMOUNT == 0
        return vec3(0.0, 0.0, 0.0);
    #endif
    if (VdotU < 0.0) return vec3(0.0);

    starCoord *= 0.2;
    float starFactor = 1024.0;
    starCoord = floor(starCoord * starFactor) / starFactor;

    float star = 1.0;
    star *= GetStarNoise(starCoord.xy);
    star *= GetStarNoise(starCoord.xy+0.1);
    star *= GetStarNoise(starCoord.xy+0.23);

    #if NIGHT_STAR_AMOUNT == 1
        star -= 0.82;
        star *= 2.0;
    #elif NIGHT_STAR_AMOUNT == 2
        star -= 0.7;
    #elif NIGHT_STAR_AMOUNT == 3
        star -= 0.62;
        star *= 0.75;
    #elif NIGHT_STAR_AMOUNT == 4
        star -= 0.52;
        star *= 0.55;
    #endif
    star = max0(star);
    star *= star;

    star *= min1(VdotU * 3.0) * max0(1.0 - pow(abs(VdotS) * 1.002, 100.0));
    star *= invRainFactor * pow2(pow2(invNoonFactor2)) * (1.0 - 0.5 * sunVisibility);

    return 40.0 * star * vec3(0.38, 0.4, 0.5);
}

float GetGalaxyNoise(vec2 coord) {
    vec2 cell = floor(coord);
    vec2 blend = fract(coord);
    blend = blend * blend * (3.0 - 2.0 * blend);

    float bottom = mix(GetStarNoise(cell), GetStarNoise(cell + vec2(1.0, 0.0)), blend.x);
    float top = mix(GetStarNoise(cell + vec2(0.0, 1.0)), GetStarNoise(cell + vec2(1.0)), blend.x);
    return mix(bottom, top, blend.y);
}

vec3 GetMilkyWay(vec3 viewDir, float VdotU, float VdotS) {
    if (VdotU < -0.05) return vec3(0.0);

    vec3 skyDir = normalize(viewDir);
    vec3 eastAxis = normalize(gbufferModelView[0].xyz);
    vec3 galacticNormal = normalize(0.74 * upVec + 0.45 * sunVec + 0.50 * eastAxis);
    vec3 galacticAxis = normalize(cross(galacticNormal, upVec));
    vec3 galacticSide = normalize(cross(galacticNormal, galacticAxis));

    float signedDistance = dot(skyDir, galacticNormal);
    float planeDistance = abs(signedDistance);

    // Projecting directly onto the galactic basis keeps the pattern continuous around the sphere.
    float alongPlane = dot(skyDir, galacticAxis);
    float acrossPlane = dot(skyDir, galacticSide);
    vec2 cloudCoord = vec2(alongPlane * 3.4 + signedDistance * 2.2,
                           acrossPlane * 3.4 + signedDistance * 3.1);
    float cloudLarge = GetGalaxyNoise(cloudCoord + vec2(3.7, 8.2));
    float cloudMedium = cloudLarge * cloudLarge * (3.0 - 2.0 * cloudLarge);
    float cloudShape = mix(cloudLarge, cloudMedium, 0.35);

    float wideBand = 1.0 - smoothstep(0.10, 0.48, planeDistance);
    float denseBand = 1.0 - smoothstep(0.035, 0.24, planeDistance);
    vec3 galacticCenterDir = normalize(0.94 * galacticAxis + 0.34 * galacticSide);
    float galacticCenter = smoothstep(-0.15, 0.82, dot(skyDir, galacticCenterDir));
    float dustWarp = signedDistance + (cloudLarge - 0.5) * 0.055 + (cloudMedium - 0.5) * 0.025;
    float dustLane = 1.0 - smoothstep(0.022, 0.09, abs(dustWarp));
    float cloudyDetail = smoothstep(0.22, 0.68, cloudShape);

    float galaxy = wideBand * (0.16 + 0.84 * cloudyDetail);
    galaxy += denseBand * (0.28 + 0.62 * galacticCenter) * (0.3 + 0.7 * cloudLarge);
    galaxy *= 1.0 - dustLane * (0.58 + 0.18 * cloudMedium);
    galaxy *= smoothstep(-0.05, 0.18, VdotU);
    galaxy *= invRainFactor * pow2(pow2(invNoonFactor2)) * (1.0 - 0.5 * sunVisibility);
    galaxy *= max0(1.0 - pow(abs(VdotS) * 1.002, 40.0)) * (1.0 - maxBlindnessDarkness);

    vec3 outerColor = vec3(0.07, 0.085, 0.13);
    vec3 coreColor = vec3(0.22, 0.125, 0.105);
    return galaxy * mix(outerColor, coreColor, galacticCenter * (0.45 + 0.55 * cloudLarge));
}
