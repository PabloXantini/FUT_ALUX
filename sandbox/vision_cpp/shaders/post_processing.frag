#version 330 core
out vec4 FragColor;
in vec2 TexCoords;

// --- Fisheye ---
uniform sampler2D screenTexture;  // Current frame
uniform float k;                  // Barrel distortion factor (negative = barrel, positive = pincushion)
uniform float zoom;               // Zoom compensation

// --- Motion Blur ---
uniform sampler2D historyTex[7];  // Previous frames history (max 7 slots)
uniform int motionBlurSamples;    // Cuántos slots de historial usar (0 = desactivado)
uniform float motionBlurStrength; // 0.0 = sin blur, 1.0 = blur máximo

void main() {
    // 1) Apply fisheye distortion to UVs
    vec2 uv = TexCoords - 0.5;
    float r2 = dot(uv, uv);
    vec2 distortedUV = uv * (1.0 - k * r2);
    distortedUV = (distortedUV / zoom) + 0.5;
    // 2) Out of range → black
    if (distortedUV.x < 0.0 || distortedUV.x > 1.0 ||
        distortedUV.y < 0.0 || distortedUV.y > 1.0) {
        FragColor = vec4(0.0, 0.0, 0.0, 1.0);
        return;
    }
    // 3) Sample current frame (with distorted UVs)
    vec4 currentColor = texture(screenTexture, distortedUV);
    if (motionBlurSamples <= 0) {
        FragColor = currentColor;
        return;
    }
    // 4) Accumulate history with exponential decay
    vec4 accumColor = vec4(0.0);
    float totalWeight = 0.0;
    for (int i = 0; i < motionBlurSamples; i++) {
        // Weight decays with time (most recent frame = highest weight)
        float w = 1.0 / float(i + 1);
        vec4 histColor;
        // GLSL 3.30 does not allow indexing arrays of samplers with non-constant variable,
        // so we use a chain of if/else
        if      (i == 0) histColor = texture(historyTex[0], distortedUV);
        else if (i == 1) histColor = texture(historyTex[1], distortedUV);
        else if (i == 2) histColor = texture(historyTex[2], distortedUV);
        else if (i == 3) histColor = texture(historyTex[3], distortedUV);
        else if (i == 4) histColor = texture(historyTex[4], distortedUV);
        else if (i == 5) histColor = texture(historyTex[5], distortedUV);
        else             histColor = texture(historyTex[6], distortedUV);
        accumColor  += histColor * w;
        totalWeight += w;
    }
    accumColor /= totalWeight;

    // 5) Mezclar frame actual con historial segun strength
    FragColor = mix(currentColor, accumColor, motionBlurStrength);
}
