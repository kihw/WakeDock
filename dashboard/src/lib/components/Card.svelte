<script lang="ts">
  export let title: string = '';
  export let subtitle: string = '';
  export let padding: boolean = true;
  export let className: string = '';

  // Allow `class` prop as well
  let cssClass = '';
  export { cssClass as class };
</script>

<div class="bg-white shadow rounded-lg {padding ? 'p-6' : ''} {className} {cssClass}">
  {#if title || subtitle}
    <div class="mb-4">
      {#if title}
        <h3 class="text-lg font-medium text-gray-900">{title}</h3>
      {/if}
      {#if subtitle}
        <p class="mt-1 text-gray-600">{subtitle}</p>
      {/if}
    </div>
  {/if}
  <slot />
</div>
