<template>
  <div class="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-5 mb-5">
    <!-- ???? ??? ?? ?? ?? -->
    <div
      v-if="users.length === 0"
      @click="openModal"
      class="flex flex-col items-center justify-center border-2 border-dashed border-blue-500 rounded-lg h-80 cursor-pointer hover:bg-blue-100"
    >
      <div class="text-5xl text-blue-500">+</div>
      <div class="mt-3 text-lg font-semibold text-blue-500">?? ????</div>
    </div>
    <!-- ??? ?? ?? -->
    <div
      v-for="user in users"
      :key="user.id"
      class="border rounded-lg shadow-sm p-4 text-center"
    >
      <img
        v-if="user.images && user.images.length > 0"
        :src="user.images[0].url"
        alt="User Image"
        class="w-full h-72 object-cover rounded-lg"
      />
      <div
        v-else
        class="w-full h-72 bg-gray-200 flex items-center justify-center text-gray-500"
      >
        ??? ??
      </div>
      <div class="mt-3 text-lg font-bold">{{ user.name }}</div>
      <div class="mt-2 text-sm text-gray-700">
        <p><strong>??:</strong> {{ user.position }}</p>
        <p>
          <strong>???:</strong>
          {{ user.phone ? user.phone : "??" }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  users: {
    type: Array,
    default: () => [],
  },
  openModal: {
    type: Function,
    default: () => {},
  },
});
</script>
