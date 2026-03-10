<template>
  <div ref="container" class="w-full h-[400px] bg-black rounded-lg relative">
    <div
      v-if="isLoading"
      class="absolute inset-0 flex items-center justify-center text-white text-sm"
    >
      <span>라이다 데이터 로딩 중...</span>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';
import * as THREE from 'three';
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls';
import { PCDLoader } from 'three/examples/jsm/loaders/PCDLoader';

const props = defineProps({
  robotSeq: {
    type: Number,
    required: true
  }
});

const emit = defineEmits(['lidar-update']);

const container = ref(null);
const isLoading = ref(true);
let scene, camera, renderer, controls;
let pointCloud;
let eventSource = null;
let isSSEFailed = false;
let isLiveDataEnabled = false;

// Three.js 초기화
const initThree = () => {
  scene = new THREE.Scene();
  scene.background = new THREE.Color(0x000000);

  camera = new THREE.PerspectiveCamera(
    75,
    container.value.clientWidth / container.value.clientHeight,
    0.1,
    1000
  );
  camera.position.set(5, 5, 5);
  camera.lookAt(0, 0, 0);

  renderer = new THREE.WebGLRenderer({ antialias: true });
  renderer.setSize(container.value.clientWidth, container.value.clientHeight);
  container.value.appendChild(renderer.domElement);

  controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;

  // 좌표축 헬퍼
  const axesHelper = new THREE.AxesHelper(5);
  scene.add(axesHelper);

  // 초기 포인트클라우드
  const geometry = new THREE.BufferGeometry();
  const material = new THREE.PointsMaterial({ size: 0.05, vertexColors: true });
  pointCloud = new THREE.Points(geometry, material);
  scene.add(pointCloud);

  animate();
};

// 포인트클라우드 업데이트
const updatePointCloud = (pcdData) => {
  if (!pcdData || !pcdData.positions || pcdData.positions.length === 0) return;

  const positions = new Float32Array(pcdData.positions);
  const colors = new Float32Array(pcdData.positions.length);

  for (let i = 0; i < pcdData.intensities.length; i++) {
    const colorIndex = i * 3;
    colors[colorIndex] = 1.0;
    colors[colorIndex + 1] = 1.0;
    colors[colorIndex + 2] = 1.0;
  }

  pointCloud.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
  pointCloud.geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
  pointCloud.geometry.computeBoundingSphere();
  isLoading.value = false;
};

// 정적 PCD 파일 로드
const loadStaticPCD = () => {
  const loader = new PCDLoader();
  loader.load(
    '/media/persons_image/map.pcd',
    (points) => {
      if (pointCloud) scene.remove(pointCloud);
      pointCloud = points;
      pointCloud.material.size = 0.05;
      scene.add(pointCloud);

      // 중앙 정렬
      const box = new THREE.Box3().setFromObject(pointCloud);
      const center = box.getCenter(new THREE.Vector3());
      pointCloud.position.sub(center);
      isLoading.value = false;
    },
    (xhr) => {
      console.log((xhr.loaded / xhr.total * 100).toFixed(1) + '% 로드');
    },
    (error) => {
      console.warn('PCD 파일 없음, 빈 시작:', error);
      isLoading.value = false;
    }
  );
};

// SSE 라이브 데이터 연결
const connectToLidarSSE = () => {
  if (isLiveDataEnabled) return;
  isLiveDataEnabled = true;

  eventSource = new EventSource(`/api/v1/lidar/sse/${props.robotSeq}`);

  eventSource.onmessage = (event) => {
    const data = JSON.parse(event.data);
    if (data.pcd) {
      updatePointCloud(data.pcd);
      emit('lidar-update', data.pcd.points, data.timestamp);
    }
  };

  eventSource.onerror = (error) => {
    console.warn('라이다 SSE 연결 오류 - 정적 PCD로 대체:', error);
    if (!isSSEFailed) {
      isSSEFailed = true;
      eventSource.close();
      isLiveDataEnabled = false;
      loadStaticPCD();
    }
  };
};

// 애니메이션 루프
const animate = () => {
  requestAnimationFrame(animate);
  controls.update();
  renderer.render(scene, camera);
};

// 리사이즈 핸들러
const handleResize = () => {
  if (!container.value) return;
  const width = container.value.clientWidth;
  const height = container.value.clientHeight;
  camera.aspect = width / height;
  camera.updateProjectionMatrix();
  renderer.setSize(width, height);
};

onMounted(() => {
  initThree();
  // SSE 연결 시도, 실패 시 정적 PCD 로드
  connectToLidarSSE();
  window.addEventListener('resize', handleResize);
});

onUnmounted(() => {
  if (eventSource) {
    eventSource.close();
    isLiveDataEnabled = false;
  }
  window.removeEventListener('resize', handleResize);
  if (renderer) renderer.dispose();
  if (container.value) container.value.innerHTML = '';
  isSSEFailed = false;
});

watch(() => props.robotSeq, () => {
  isSSEFailed = false;
  isLiveDataEnabled = false;
  if (eventSource) {
    eventSource.close();
    eventSource = null;
  }
  connectToLidarSSE();
});
</script>

<style scoped>
.point-cloud-container {
  position: relative;
  width: 100%;
  height: 400px;
}
</style>
