/**
 * CloudShader — Vanilla JS WebGL cloud background
 * Ported from Aceternity UI's React CloudShader component.
 * Renders animated, drifting volumetric clouds using GLSL shaders.
 */
(function () {
  'use strict';

  const VERT = `
attribute vec2 a_pos;
varying vec2 v_uv;
void main() {
  v_uv = a_pos * 0.5 + 0.5;
  gl_Position = vec4(a_pos, 0.0, 1.0);
}
`;

  const FRAG = `
precision highp float;

varying vec2 v_uv;

uniform vec2 u_res;
uniform float u_time;
uniform float u_count;
uniform vec3 u_cloud;
uniform vec3 u_skyTop;
uniform vec3 u_skyBottom;

const mat2 R = mat2(0.80, 0.60, -0.60, 0.80);

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(41.31, 289.17))) * 26737.367);
}

float vnoise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  f = f * f * (3.0 - 2.0 * f);
  float a = hash(i);
  float b = hash(i + vec2(1.0, 0.0));
  float c = hash(i + vec2(0.0, 1.0));
  float d = hash(i + vec2(1.0, 1.0));
  return mix(mix(a, b, f.x), mix(c, d, f.x), f.y);
}

float fbm(vec2 p) {
  float sum = 0.0;
  float amp = 0.5;
  for (int i = 0; i < 4; i++) {
    sum += amp * vnoise(p);
    p = R * p * 2.03 + 19.19;
    amp *= 0.5;
  }
  return sum;
}

float billow(vec2 p) {
  float sum = 0.0;
  float amp = 0.5;
  for (int i = 0; i < 5; i++) {
    sum += amp * (1.0 - abs(2.0 * vnoise(p) - 1.0));
    p = R * p * 2.11 + 13.37;
    amp *= 0.5;
  }
  return sum;
}

float cloudDensity(vec2 p, vec2 c, vec2 r, float seed, float t) {
  vec2 q = p - c;
  float ry = q.y > 0.0 ? r.y : r.y * 0.42;
  float env = 1.0 - length(vec2(q.x / r.x, q.y / ry));
  if (env < -0.35) return 0.0;
  vec2 dp = q * (2.4 / r.x) + seed;
  dp += 0.6 * vec2(
    fbm(dp * 1.4 + t * 0.04),
    fbm(dp * 1.4 + 7.7 - t * 0.03)
  );
  float detail = billow(dp * 1.6);
  return env + (detail - 0.62) * 0.62;
}

vec3 shadeCloud(vec3 color, vec3 sky, vec2 p, vec2 c, vec2 r, float seed, float t, float dist) {
  float d = cloudDensity(p, c, r, seed, t);
  if (d < 0.02) return color;
  float dUp = cloudDensity(p + vec2(0.0, r.y * 0.55), c, r, seed, t);
  float occl = clamp((dUp - d) * 1.1 + d * 0.55, 0.0, 1.0);
  vec3 lit = u_cloud * 1.04;
  vec3 shadow = mix(u_cloud * 0.60, sky, 0.38);
  vec3 cloudCol = mix(lit, shadow, occl * 0.85);
  float alpha = smoothstep(0.02, 0.38, d);
  float rim = smoothstep(0.02, 0.14, d) * (1.0 - smoothstep(0.14, 0.40, d));
  cloudCol += rim * 0.10;
  cloudCol = mix(cloudCol, sky, dist * 0.35);
  alpha *= mix(1.0, 0.8, dist);
  return mix(color, cloudCol, alpha);
}

vec3 cloudPass(vec3 color, vec3 sky, vec2 p, float aspect, float t,
               float spd, float phase, float y, vec2 r, float seed, float dist) {
  float cx = mix(-r.x - 0.25, aspect + r.x + 0.25, fract(t * spd + phase));
  float cy = y + sin(t * 0.05 + phase * 6.2831) * 0.012;
  return shadeCloud(color, sky, p, vec2(cx, cy), r, seed, t, dist);
}

void main() {
  float aspect = u_res.x / u_res.y;
  vec2 p = vec2(v_uv.x * aspect, v_uv.y);
  float t = u_time;
  vec3 sky = mix(u_skyBottom, u_skyTop, v_uv.y);
  vec3 color = sky;
  color = mix(color, u_skyBottom * 1.06, smoothstep(0.35, 0.0, v_uv.y) * 0.5);
  vec2 sunPos = vec2(aspect * 0.78, 0.92);
  float sunDist = length(p - sunPos);
  color += vec3(1.0, 0.95, 0.82) * exp(-sunDist * sunDist * 5.0) * 0.28;

  float cirrusBand = smoothstep(0.55, 0.8, v_uv.y) * (1.0 - smoothstep(0.9, 1.0, v_uv.y));
  if (cirrusBand > 0.01) {
    float streak = fbm(vec2(p.x * 1.6 - t * 0.006, p.y * 12.0));
    float wisp = smoothstep(0.52, 0.78, streak) * cirrusBand;
    color = mix(color, u_cloud * 0.98, wisp * 0.35);
  }

  if (u_count > 5.5) {
    color = cloudPass(color, sky, p, aspect, t, 0.006, 0.10, 0.84, vec2(0.20, 0.10), 43.7, 1.0);
  }
  if (u_count > 4.5) {
    color = cloudPass(color, sky, p, aspect, t, 0.008, 0.62, 0.73, vec2(0.24, 0.12), 71.3, 0.85);
  }
  if (u_count > 3.5) {
    color = cloudPass(color, sky, p, aspect, t, 0.011, 0.33, 0.60, vec2(0.34, 0.16), 17.3, 0.55);
  }
  if (u_count > 2.5) {
    color = cloudPass(color, sky, p, aspect, t, 0.013, 0.80, 0.47, vec2(0.30, 0.15), 29.9, 0.45);
  }
  if (u_count > 1.5) {
    color = cloudPass(color, sky, p, aspect, t, 0.016, 0.05, 0.35, vec2(0.46, 0.20), 91.1, 0.15);
  }
  color = cloudPass(color, sky, p, aspect, t, 0.020, 0.48, 0.20, vec2(0.56, 0.24), 57.2, 0.0);

  gl_FragColor = vec4(color, 1.0);
}
`;

  function parseHex(hex) {
    hex = hex.replace('#', '');
    if (hex.length === 3) {
      hex = hex[0]+hex[0]+hex[1]+hex[1]+hex[2]+hex[2];
    }
    return [
      parseInt(hex.slice(0,2), 16) / 255,
      parseInt(hex.slice(2,4), 16) / 255,
      parseInt(hex.slice(4,6), 16) / 255
    ];
  }

  function compileShader(gl, type, source) {
    var s = gl.createShader(type);
    if (!s) return null;
    gl.shaderSource(s, source);
    gl.compileShader(s);
    if (!gl.getShaderParameter(s, gl.COMPILE_STATUS)) {
      console.error('Shader compile error:', gl.getShaderInfoLog(s));
      gl.deleteShader(s);
      return null;
    }
    return s;
  }

  function initCloudShader(canvasId, opts) {
    opts = opts || {};
    var speed      = opts.speed       || 1;
    var count      = opts.count       || 6;
    var cloudColor = opts.cloudColor  || '#fbf8f2';
    var skyTop     = opts.skyTopColor || '#3876ba';
    var skyBottom  = opts.skyBottomColor || '#8cbfe8';

    var canvas = document.getElementById(canvasId);
    if (!canvas) return;

    var gl = canvas.getContext('webgl', {
      alpha: false,
      antialias: false,
      premultipliedAlpha: false
    });
    if (!gl) return;

    var vert = compileShader(gl, gl.VERTEX_SHADER, VERT);
    var frag = compileShader(gl, gl.FRAGMENT_SHADER, FRAG);
    if (!vert || !frag) return;

    var program = gl.createProgram();
    gl.attachShader(program, vert);
    gl.attachShader(program, frag);
    gl.bindAttribLocation(program, 0, 'a_pos');
    gl.linkProgram(program);
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) {
      console.error('Program link error:', gl.getProgramInfoLog(program));
      return;
    }
    gl.useProgram(program);

    var buffer = gl.createBuffer();
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer);
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1,-1, 3,-1, -1,3]), gl.STATIC_DRAW);
    gl.enableVertexAttribArray(0);
    gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0);

    var loc = {
      res:       gl.getUniformLocation(program, 'u_res'),
      time:      gl.getUniformLocation(program, 'u_time'),
      count:     gl.getUniformLocation(program, 'u_count'),
      cloud:     gl.getUniformLocation(program, 'u_cloud'),
      skyTop:    gl.getUniformLocation(program, 'u_skyTop'),
      skyBottom: gl.getUniformLocation(program, 'u_skyBottom')
    };

    var reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    function resize() {
      var dpr = Math.min(window.devicePixelRatio || 1, 2);
      var width = canvas.clientWidth || canvas.parentElement.clientWidth || window.innerWidth;
      var height = canvas.clientHeight || canvas.parentElement.clientHeight || 550;
      var w = Math.max(1, Math.floor(width * dpr));
      var h = Math.max(1, Math.floor(height * dpr));
      if (canvas.width !== w || canvas.height !== h) {
        canvas.width = w;
        canvas.height = h;
      }
      gl.viewport(0, 0, w, h);
      gl.uniform2f(loc.res, w, h);
    }

    if (window.ResizeObserver) {
      var ro = new ResizeObserver(resize);
      ro.observe(canvas.parentElement || canvas);
    }
    window.addEventListener('resize', resize);
    resize();

    var cloud = parseHex(cloudColor);
    var top   = parseHex(skyTop);
    var bot   = parseHex(skyBottom);

    var start = performance.now();
    var frame = 0;

    function draw(now) {
      var elapsed = reduceMotion ? 0 : ((now - start) / 1000) * speed;
      gl.uniform1f(loc.time, elapsed);
      gl.uniform1f(loc.count, Math.min(6, Math.max(1, count)));
      gl.uniform3f(loc.cloud, cloud[0], cloud[1], cloud[2]);
      gl.uniform3f(loc.skyTop, top[0], top[1], top[2]);
      gl.uniform3f(loc.skyBottom, bot[0], bot[1], bot[2]);
      gl.drawArrays(gl.TRIANGLES, 0, 3);
      frame = requestAnimationFrame(draw);
    }

    frame = requestAnimationFrame(draw);
  }

  // Auto-init when DOM is ready
  function startShader() {
    initCloudShader('cloud-shader-canvas', {
      speed: 1,
      count: 6,
      cloudColor:    '#fbf8f2',
      skyTopColor:   '#3876ba',
      skyBottomColor:'#8cbfe8'
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', startShader);
  } else {
    startShader();
  }
})();

