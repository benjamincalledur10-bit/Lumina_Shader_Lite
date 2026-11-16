// Original Lumina adapter for Voxy's VoxyFragmentParameters callback (API 3).
#define LUMINA_VOXY_PATCH
#define FRAGMENT_SHADER
#define texture2D texture
#define texture2DLod textureLod
#define shadow2D(s, p) vec4(texture(s, p))

mat4 gbufferModelView = vxModelView;
mat4 gbufferModelViewInverse = vxModelViewInv;
mat4 gbufferProjection = vxProj;
mat4 gbufferProjectionInverse = vxProjInv;

#include "/lib/common.glsl"

// LOD faces have no normal maps, tangent frame or per-vertex texture derivatives.
#undef CUSTOM_PBR
#undef GENERATED_NORMALS
#undef DO_PIXELATION_EFFECTS
#undef DISTANT_LIGHT_BOKEH

vec3 upVec = normalize(gbufferModelView[1].xyz);
vec3 eastVec = normalize(gbufferModelView[0].xyz);
vec3 northVec = normalize(gbufferModelView[2].xyz);
vec3 VoxySunVector() {
    vec2 rotation = vec2(cos(sunPathRotation * 0.01745329251994),
                        -sin(sunPathRotation * 0.01745329251994));
    #ifdef OVERWORLD
        float angle = fract(timeAngle - 0.25);
        angle = (angle + (cos(angle * pi) * -0.5 + 0.5 - angle) / 3.0) * (2.0 * pi);
        vec3 direction = vec3(-sin(angle), cos(angle) * rotation);
    #else
        vec3 direction = vec3(0.0, rotation);
    #endif
    return normalize(mat3(gbufferModelView) * direction);
}
vec3 sunVec = VoxySunVector();
float SdotU = dot(sunVec, upVec);
float sunVisibility = clamp(SdotU + 0.0625, 0.0, 0.125) / 0.125;
float sunVisibility2 = sunVisibility * sunVisibility;
float sunFactor = SdotU < 0.0 ? clamp(SdotU + 0.375, 0.0, 0.75) / 0.75 : sunVisibility;
float shadowTime = pow(abs(sunVisibility - 0.5) * 2.0, 4.0);
#ifdef OVERWORLD
    vec3 lightVec = sunVec * ((timeAngle < 0.5325 || timeAngle > 0.9675) ? 1.0 : -1.0);
#else
    vec3 lightVec = sunVec;
#endif
float NdotU, NdotUmax0;
vec3 normal;
vec4 glColor;

#include "/lib/util/spaceConversion.glsl"
#include "/lib/util/dither.glsl"
// Treat LOD lighting like DH: no near shadow-map sampling beyond its coverage.
#define DH_TERRAIN
#include "/lib/lighting/mainLighting.glsl"

#ifdef LUMINA_VOXY_TRANSLUCENT
    struct LuminaVoxyFog { float start; float scale; };
    LuminaVoxyFog luminaVoxyFog = LuminaVoxyFog(fogStart, 1.0 / max(fogEnd - fogStart, 0.0001));
    #define gl_Fog luminaVoxyFog
    #include "/lib/atmospherics/fog/mainFog.glsl"
#endif
#ifdef TAA
    #include "/lib/antialiasing/jitter.glsl"
#endif

layout(location = 0) out vec4 voxyColor;
#ifndef LUMINA_VOXY_TRANSLUCENT
    layout(location = 1) out vec4 voxyMaterial;
#endif

void voxy_emitFragment(VoxyFragmentParameters parameters) {
    vec2 screen = gl_FragCoord.xy / vec2(viewWidth, viewHeight);
    #ifdef TAA
        screen = TAAJitter(screen, -0.5);
    #endif
    // Voxy converts gl_FragCoord to conventional OpenGL depth before compiling.
    vec4 position = vxProjInv * vec4(screen * 2.0 - 1.0, gl_FragCoord.z * 2.0 - 1.0, 1.0);
    vec3 viewPos = position.xyz / position.w;
    vec3 playerPos = ViewToPlayer(viewPos);
    float distanceToCamera = length(viewPos);
    // Voxy face order: -Y,+Y,-Z,+Z,-X,+X.
    uint axis = parameters.face >> 1u;
    vec3 worldNormal = axis == 0u ? vec3(0, 1, 0) : (axis == 1u ? vec3(0, 0, 1) : vec3(1, 0, 0));
    worldNormal *= (parameters.face & 1u) == 0u ? -1.0 : 1.0;
    normal = normalize(mat3(gbufferModelView) * worldNormal);
    NdotU = dot(normal, upVec);
    NdotUmax0 = max(NdotU, 0.0);
    vec2 lightmap = clamp((parameters.lightMap - 0.03125) * 1.06667, 0.0, 1.0);
    vec4 color = parameters.sampledColour * parameters.tinting;
    glColor = parameters.tinting;
    #ifndef LUMINA_VOXY_TRANSLUCENT
        color.a = 1.0;
    #endif
    int material = int(parameters.customId);
    float emission = 0.0;
    if (material == 10068) emission = min(3.75 * LAVA_EMISSIVE_INTENSITY * LAVA_BRIGHTNESS * 0.01, LAVA_EMISSION_LIMIT);
    if (material == 10412 || material == 10028) emission = 2.5;
    vec3 shadowMult = vec3(1.0);
    int subsurface = material == 10009 ? 1 : 0;
    DoLighting(color, shadowMult, playerPos, viewPos, distanceToCamera, normal, normal, 0.5,
               worldNormal, lightmap, false, false, true, false, subsurface, 0.0, 0.0, emission);
    #ifdef LUMINA_VOXY_TRANSLUCENT
        vec3 direction = normalize(viewPos);
        float skyFade = 0.0;
        float alpha = color.a;
        #ifdef ATM_COLOR_MULTS
            atmColorMult = GetAtmColorMult();
        #endif
        DoFog(color, skyFade, distanceToCamera, playerPos, dot(direction, upVec),
              dot(direction, sunVec), Bayer64(gl_FragCoord.xy), false, 0.0);
        color.a = alpha * (1.0 - skyFade);
    #else
        // Zero roughness/mask avoids interpreting simplified LODs as near PBR surfaces.
        voxyMaterial = vec4(0.0, 0.0, lightmap.y, 1.0);
    #endif
    voxyColor = color;
}
