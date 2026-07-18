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

vec3 GetMilkyWay(vec3 viewDir, float VdotU, float VdotS) {
    if (VdotU < -0.05) return vec3(0.0);

    // A cheap analytic galactic plane: no texture samples, loops or volumetric noise.
    vec3 eastAxis = normalize(gbufferModelView[0].xyz);
    vec3 galacticNormal = normalize(0.48 * upVec + 0.28 * sunVec + 0.83 * eastAxis);
    float planeDistance = abs(dot(normalize(viewDir), galacticNormal));

    float wideBand = 1.0 - smoothstep(0.05, 0.32, planeDistance);
    float brightCore = 1.0 - smoothstep(0.025, 0.12, planeDistance);
    float dustLane = 1.0 - smoothstep(0.0, 0.035, planeDistance);
    float structure = 0.82 + 0.18 * sin(dot(viewDir, vec3(12.0, 19.0, 7.0)));

    float galaxy = (0.45 * wideBand + 0.55 * brightCore) * (1.0 - 0.72 * dustLane);
    galaxy *= structure * smoothstep(-0.05, 0.22, VdotU);
    galaxy *= invRainFactor * pow2(pow2(invNoonFactor2)) * (1.0 - 0.5 * sunVisibility);
    galaxy *= max0(1.0 - pow(abs(VdotS) * 1.002, 40.0)) * (1.0 - maxBlindnessDarkness);

    return galaxy * vec3(0.028, 0.033, 0.045);
}
