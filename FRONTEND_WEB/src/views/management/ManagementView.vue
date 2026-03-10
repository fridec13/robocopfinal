<template>
  <div class="h-full overflow-y-auto bg-gray-100 p-5">
    <div class="border-b pb-2 mb-4">
      <h2 class="text-2xl font-bold text-gray-800">관리</h2>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- 계정 관리 -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h3 class="text-lg font-semibold mb-4">계정 관리</h3>
        <div class="space-y-3">
          <button
            @click="showPasswordChange = true"
            class="w-full py-2 px-4 bg-blue-500 text-white rounded hover:bg-blue-600"
          >
            비밀번호 재설정
          </button>
          <button
            @click="handleLogout"
            class="w-full py-2 px-4 bg-red-500 text-white rounded hover:bg-red-600"
          >
            로그아웃
          </button>
        </div>
      </div>

      <!-- 사용자 관리 -->
      <div class="bg-white rounded-lg shadow-md p-6">
        <h3 class="text-lg font-semibold mb-4">사용자 관리</h3>
        <UserList />
      </div>
    </div>

    <PasswordChange
      :isOpen="showPasswordChange"
      @close="showPasswordChange = false"
    />
  </div>
</template>

<script setup>
import { ref } from 'vue';
import { useRouter } from 'vue-router';
import PasswordChange from '@/components/management/PasswordChange.vue';
import UserList from '@/components/enrollment/UserList.vue';

const router = useRouter();
const showPasswordChange = ref(false);

const handleLogout = () => {
  localStorage.removeItem('accessToken');
  localStorage.removeItem('refreshToken');
  router.push('/login');
};
</script>
