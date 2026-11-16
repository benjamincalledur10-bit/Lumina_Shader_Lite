// Flywheel's additive, lightning, glint and crumbling materials use their own
// blend modes. Write only scene color so their blending cannot corrupt Gbuffer
// material metadata or the translucent-transmission buffer.
#include "/lib/common.glsl"

#ifdef FRAGMENT_SHADER
in vec2 texCoord;

void main() {
    vec4 color;
    vec2 lightmap;
    float ao;
    vec4 overlayColor;
    clrwl_computeFragment(texture2D(tex, texCoord), color, lightmap, ao, overlayColor);
    color.rgb = mix(color.rgb, overlayColor.rgb, overlayColor.a);
    // These passes precede deferred lighting/fog; keep the material's blend data.
    /* DRAWBUFFERS:0 */
    gl_FragData[0] = color;
}
#endif

#ifdef VERTEX_SHADER
out vec2 texCoord;
#ifdef TAA
    #include "/lib/antialiasing/jitter.glsl"
#endif

void main() {
    texCoord = (gl_TextureMatrix[0] * gl_MultiTexCoord0).xy;
    gl_Position = gl_ProjectionMatrix * gl_ModelViewMatrix * gl_Vertex;
    #ifdef TAA
        gl_Position.xy = TAAJitter(gl_Position.xy, gl_Position.w);
    #endif
}
#endif
