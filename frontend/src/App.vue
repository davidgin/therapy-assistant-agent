<template>
  <div id="app">
    <header class="bg-blue-600 text-white p-4">
      <h1 class="text-2xl font-bold">Therapy Assistant Agent</h1>
    </header>
    
    <main class="container mx-auto p-4">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
// Main App component for Therapy Assistant Agent
</script>

<style>
#app {
  min-height: 100vh;
  background-color: #f5f5f5;
}
</style>