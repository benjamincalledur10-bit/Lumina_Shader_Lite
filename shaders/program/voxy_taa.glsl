{
    #if TAA_MODE >= 1 && DETAIL_QUALITY >= 1 && TAA_JITTER > 0
        vec2 offsets[8] = vec2[8](
            vec2(0.125, -0.375), vec2(-0.125, 0.375),
            vec2(0.625, 0.125), vec2(0.375, -0.625),
            vec2(-0.625, 0.625), vec2(-0.875, -0.125),
            vec2(0.375, -0.875), vec2(0.875, 0.875));
        vec2 offset = offsets[int(framemod8)] / vec2(viewWidth, viewHeight);
        #if TAA_JITTER == 1
            offset *= 0.125;
        #elif TAA_JITTER == 2
            offset *= 0.33;
        #endif
        return offset;
    #else
        return vec2(0.0);
    #endif
}
