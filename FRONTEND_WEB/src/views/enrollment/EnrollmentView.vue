<template>
  <div class="p-5 font-sans max-h-screen overflow-y-auto">
    <div class="flex items-center justify-between mb-5">
      <h1 class="text-2xl font-bold">?�록???�용??명단</h1>
      <button
        v-if="users.length > 0"
        @click="openModal"
        class="px-4 py-2 bg-blue-500 text-white rounded-md shadow-md hover:bg-blue-600 transition"
      >
        ?�록?�기
      </button>
    </div>

    <!-- ?�용??목록 ?�시 -->
    <UserList :users="users" :openModal="openModal" />

    <!-- ?�록 모달 -->
    <EnrollModal
      :showModal="showModal"
      :formData="formData"
      @closeModal="closeModal"
      @submitForm="addUser"
    />
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue';
import EnrollModal from '@/components/enrollment/EnrollModal.vue';
import UserList from '@/components/enrollment/UserList.vue';
import axios from 'axios';

// ?�용??목록 (초기??�?배열)
const users = ref([]);

// 모달 ?�시 ?��?
const showModal = ref(false);

// ???�이??(?��?지 ?�일?� ?�러 �?첨�? 가??
const formData = reactive({
  personName: '',
  personPosition: '',
  personPhone: '',
  images: [], // ?�러 ?�일 객체�??�??
});

// 모달 ?�기/?�기, ??리셋 ?�수
const openModal = () => {
  showModal.value = true;
};

const resetForm = () => {
  formData.personName = '';
  formData.personPosition = '';
  formData.personPhone = '';
  formData.images = [];
};

const closeModal = () => {
  showModal.value = false;
  resetForm();
};

// ?�용??추�? ?�수 (axios, then/catch ?�용)
const addUser = (newUser) => {
  if (!newUser.images || newUser.images.length === 0) {
    console.error("?��?지 ?�일???�요?�니??");
    return;
  }

  // ?�일�?기�? ?�름차순 ?�렬 ??�?번째 ?�일 ?�택
  const sortedImages = [...newUser.images].sort((a, b) =>
    a.name.localeCompare(b.name)
  );
  const selectedImage = sortedImages[0];

  // FormData 객체??값을 추�? (?�일 객체??그�?�??�송)
  const formDataToSend = new FormData();
  formDataToSend.append("personName", newUser.personName);
  formDataToSend.append("personPosition", newUser.personPosition);
  formDataToSend.append("image", selectedImage);
  formDataToSend.append("personPhone", newUser.personPhone);
  formDataToSend.append("personDepartment", newUser.personDepartment || "");

  // (?�버깅용) FormData???�용??출력
  for (let [key, value] of formDataToSend.entries()) {
    console.log(key, value);
  }

  axios
    .post("https://robocop-backend-app.fly.dev/api/v1/persons", formDataToSend)
    .then((response) => {
      // API ?�답?�서 ?�?�된 ?�용??객체 추출 (?�요 ??response.data.data�?조정)
      const savedUser = response.data;
      console.log("Saved user:", savedUser);
      users.value.push(savedUser);
      closeModal();
    })
    .catch((error) => {
      console.error("Error adding user:", error);
      closeModal();
    });
};

// GET API�??�용??목록 불러?�기
const getUsers = () => {
  axios
    .get('https://robocop-backend-app.fly.dev/api/v1/persons')
    .then((response) => {
      const resData = response.data;
      // ?�답 구조: { success, status, message, timestamp, data: [ ... ] }
      if (resData && Array.isArray(resData.data)) {
        users.value = resData.data;
      } else {
        users.value = [];
      }
    })
    .catch((error) => {
      console.error("Error fetching users:", error);
      users.value = [];
    });
};

onMounted(() => {
  getUsers();
});
</script>
