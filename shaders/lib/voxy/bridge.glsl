// Reuse the existing distant-depth consumers with Voxy's native textures/matrices.
// Never redirect a real Distant Horizons installation to Voxy's buffers.
#if defined VOXY && VOXY >= 3 && !defined DISTANT_HORIZONS
    #define LUMINA_VOXY
    #define DISTANT_HORIZONS
    #define dhDepthTex vxDepthTexTrans
    #define dhDepthTex1 vxDepthTexOpaque
    #define dhProjection vxProj
    #define dhProjectionInverse vxProjInv
    #define dhPreviousProjection vxProjPrev
    #define dhRenderDistance (vxRenderDistance * 16)
#endif
