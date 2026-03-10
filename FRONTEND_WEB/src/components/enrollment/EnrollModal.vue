<template>
  <div
    v-if="showModal"
    class="fixed inset-0 flex items-center justify-center bg-black bg-opacity-50 z-50"
  >
    <div class="bg-white p-6 rounded-lg shadow-lg w-96">
      <h2 class="text-xl font-semibold mb-4">?¨Ïö©???±Î°ù</h2>
      <form @submit.prevent="submitForm" class="space-y-4">
        <div>
          <label class="block font-medium mb-1">?¥Î¶Ñ:</label>
          <input
            type="text"
            v-model="formData.personName"
            required
            class="w-full px-3 py-2 border rounded-lg focus:ring focus:ring-blue-300"
          />
        </div>
        <div>
          <label class="block font-medium mb-1">ÏßÅÍ∏â:</label>
          <input
            type="text"
            v-model="formData.personPosition"
            required
            class="w-full px-3 py-2 border rounded-lg focus:ring focus:ring-blue-300"
          />
        </div>
        <div>
          <label class="block font-medium mb-1">?¥Î???Î≤àÌò∏:</label>
          <input
            type="tel"
            v-model="formData.personPhone"
            @blur="formatPhone"
            required
            class="w-full px-3 py-2 border rounded-lg focus:ring focus:ring-blue-300"
          />
        </div>
        <div>
          <label class="block font-medium mb-1">?±Î°ù???¨ÏßÑ:</label>
          <!-- multiple ?çÏÑ±?ºÎ°ú ?¨Îü¨ ?åÏùº ?†ÌÉù ÏßÄ??-->
          <input
            type="file"
            @change="handleFileUpload"
            multiple
            accept="image/*"
            required
            class="w-full border p-2 rounded-lg cursor-pointer"
          />
        </div>
        <div class="flex justify-end space-x-2">
          <button
            type="submit"
            class="px-4 py-2 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
          >
            ?±Î°ù
          </button>
          <button
            type="button"
            @click="closeModal"
            class="px-4 py-2 bg-gray-400 text-white rounded-lg hover:bg-gray-500"
          >
            Ï∑®ÏÜå
          </button>
        </div>
      </form>
    </div>
  </div>
</template>

<script setup>
const props = defineProps({
  showModal: {
    type: Boolean,
    required: true,
  },
  formData: {
    type: Object,
    required: true,
  },
});

const emit = defineEmits(["closeModal", "submitForm"]);

const handleFileUpload = (event) => {
  props.formData.images = Array.from(event.target.files);
};

const formatPhoneNumber = (phone) => {
  const digits = phone.replace(/\D/g, "");
  if (digits.length === 11) {
    return digits.replace(/(\d{3})(\d{4})(\d{4})/, "$1-$2-$3");
  }
  return phone;
};

const formatPhone = () => {
  props.formData.personPhone = formatPhoneNumber(props.formData.personPhone);
};

const closeModal = () => {
  emit("closeModal");
};

const submitForm = () => {
  // ?¥Î???Î≤àÌò∏ ?¨Îß∑ ?ÅÏö©
  props.formData.personPhone = formatPhoneNumber(props.formData.personPhone);

  const newUser = {
    personName: props.formData.personName,
    personPosition: props.formData.personPosition,
    personPhone: props.formData.personPhone,
    images: props.formData.images, // ?¨Îü¨ ?åÏùº Í∞ùÏ≤¥ ?ÑÎã¨
    personDepartment: "",
  };

  emit("submitForm", newUser);
  emit("closeModal");
};
</script>
