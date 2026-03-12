<template>
  <div class="relative w-screen h-screen overflow-hidden bg-gray-900">
    <div class="flex h-screen w-full relative">
      <!-- Left Column -->
      <div class="w-1/2 flex flex-col items-center justify-center bg-gray-800">
        <img src="@/assets/logo.svg" alt="Robocop Logo" class="w-48 mb-6">
        <div class="text-center text-gray-200">
          <h2 class="text-2xl font-bold mb-1">스마트 보안</h2>
          <h2 class="text-2xl font-bold mb-1">로봇 관제 시스템에 오신 것을</h2>
          <h2 class="text-2xl font-bold">ROBOCOP에 오신 것을 환영합니다!</h2>
        </div>
      </div>

      <!-- Right Column -->
      <form @submit.prevent="handleLogin" class="w-1/2 flex items-center justify-center relative z-10">
        <div class="w-full max-w-md bg-white p-8 rounded-lg shadow-md bg-opacity-90">
          <h3 class="text-lg font-semibold text-gray-700 mb-2">아이디</h3>
          <input
            v-model="loginForm.username"
            type="text"
            placeholder="ID를 입력하세요"
            class="w-full p-3 mb-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-gray-500">

          <h3 class="text-lg font-semibold text-gray-700 mb-2">비밀번호</h3>
          <input
            v-model="loginForm.password"
            type="password"
            placeholder="비밀번호"
            class="w-full p-3 mb-4 border border-gray-300 rounded focus:outline-none focus:ring-2 focus:ring-gray-500">

          <button type="submit" class="w-full p-3 bg-black text-white rounded hover:bg-gray-700">로그인</button>

          <div class="mt-4 p-3 bg-gray-50 rounded border border-gray-200 text-sm text-gray-500">
            <p class="font-medium text-gray-600 mb-1">데모 계정</p>
            <p>아이디: <span class="font-mono font-semibold text-gray-700">admin</span></p>
            <p>비밀번호: <span class="font-mono font-semibold text-gray-700">admin1234</span></p>
          </div>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import axios from 'axios';

const router = useRouter();
const loginForm = ref({
  username: '',
  password: '',
});

const handleLogin = async () => {
  try {
    const params = new URLSearchParams();
    params.append('username', loginForm.value.username);
    params.append('password', loginForm.value.password);

    const response = await axios.post('/api/v1/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });

    const { accessToken, refreshToken } = response.data;
    localStorage.setItem('accessToken', accessToken);
    localStorage.setItem('refreshToken', refreshToken);
    router.push({ name: 'monitoring' });
  } catch (error) {
    console.error('로그인 실패:', error);
    alert('로그인에 실패했습니다. 다시 시도해주세요.');
  }
};
</script>
