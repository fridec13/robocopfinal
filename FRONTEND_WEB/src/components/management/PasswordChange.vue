<template>
  <div v-if="isOpen" class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50">
    <div class="bg-white p-6 rounded-lg w-96 shadow-lg">
      <h3 class="text-xl font-semibold mb-4">???? ??</h3>

      <div class="mb-3 flex flex-col">
        <label class="font-medium mb-1">?? ????</label>
        <input type="password" v-model="passwordForm.currentPassword" placeholder="?? ????"
          class="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
      </div>

      <div class="mb-3 flex flex-col">
        <label class="font-medium mb-1">? ????</label>
        <input type="password" v-model="passwordForm.newPassword" placeholder="? ????"
          class="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
      </div>

      <div class="mb-3 flex flex-col">
        <label class="font-medium mb-1">? ???? ??</label>
        <input type="password" v-model="passwordForm.confirmPassword" placeholder="? ???? ??"
          class="w-full p-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500">
      </div>

      <div class="flex justify-between mt-4">
        <button @click="changePassword" :disabled="saving"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50">
          ???? ??
        </button>
        <button @click="closeModal" class="px-4 py-2 bg-gray-400 text-white rounded-lg hover:bg-gray-500">
          ??
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue';
import axios from 'axios';

const props = defineProps({
  isOpen: Boolean,
});

const emit = defineEmits(['close']);

const passwordForm = ref({
  currentPassword: '',
  newPassword: '',
  confirmPassword: '',
});

const saving = ref(false);

const changePassword = async () => {
  if (passwordForm.value.newPassword !== passwordForm.value.confirmPassword) {
    alert('? ????? ?? ????? ???? ????.');
    return;
  }

  saving.value = true;
  try {
    await axios.post(
      '/api/v1/auth/change-password',
      {
        currentPassword: passwordForm.value.currentPassword,
        newPassword: passwordForm.value.newPassword,
        confirmPassword: passwordForm.value.confirmPassword,
      },
      {
        headers: {
          Authorization: `Bearer ${localStorage.getItem('accessToken')}`,
        },
      }
    );

    alert('????? ????? ???????.');
    closeModal();
  } catch (error) {
    console.error('???? ?? ??:', error.response?.data || error.message);
    alert(error.response?.data?.message || '???? ??? ??????. ?? ??????.');
  } finally {
    saving.value = false;
  }
};

const closeModal = () => {
  emit('close');
};
</script>
