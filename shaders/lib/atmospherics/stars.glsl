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

    vec3 worldDir = normalize(mat3(gbufferModelViewInverse) * viewDir);
    const vec3 galacticNormal = vec3(0.443, 0.365, 0.819);
    const vec3 galacticAxis = vec3(0.879, 0.0, -0.476);
    vec3 galacticSide = cross(galacticNormal, galacticAxis);

    float signedDistance = dot(worldDir, galacticNormal);
    float planeDistance = abs(signedDistance);
    float longitude = atan(dot(worldDir, galacticSide), dot(worldDir, galacticAxis));
    vec2 galaxyCoord = vec2(longitude * 0.2387, signedDistance * 2.7);

    // Three samples of the pack's existing noise texture form large clouds and fine dust.
    float cloudLarge = texture2D(noisetex, galaxyCoord * vec2(0.55, 0.8) + vec2(0.31, 0.17)).r;
    float cloudMedium = texture2D(noisetex, galaxyCoord * vec2(1.25, 1.7) + vec2(0.67, 0.43)).g;
    float cloudFine = texture2D(noisetex, galaxyCoord * vec2(2.8, 3.6) + vec2(0.13, 0.79)).b;
    float cloudShape = cloudLarge * 0.52 + cloudMedium * 0.32 + cloudFine * 0.16;

    float wideBand = 1.0 - smoothstep(0.08, 0.36, planeDistance);
    float denseBand = 1.0 - smoothstep(0.025, 0.18, planeDistance);
    float galacticCenter = 1.0 - smoothstep(0.2, 1.35, abs(longitude - 0.35));
    float dustWarp = signedDistance + (cloudMedium - 0.5) * 0.055;
    float dustLane = 1.0 - smoothstep(0.018, 0.075, abs(dustWarp));
    float cloudyDetail = smoothstep(0.28, 0.72, cloudShape);

    float galaxy = wideBand * (0.28 + 0.72 * cloudyDetail);
    galaxy += denseBand * (0.22 + 0.48 * galacticCenter) * cloudLarge;
    galaxy *= 1.0 - dustLane * (0.58 + 0.22 * cloudFine);
    galaxy *= smoothstep(-0.05, 0.18, VdotU);
    galaxy *= invRainFactor * pow2(pow2(invNoonFactor2)) * (1.0 - 0.5 * sunVisibility);
    galaxy *= max0(1.0 - pow(abs(VdotS) * 1.002, 40.0)) * (1.0 - maxBlindnessDarkness);

    vec3 outerColor = vec3(0.055, 0.072, 0.115);
    vec3 coreColor = vec3(0.18, 0.105, 0.085);
    return galaxy * mix(outerColor, coreColor, galacticCenter * (0.45 + 0.55 * cloudLarge));
}
