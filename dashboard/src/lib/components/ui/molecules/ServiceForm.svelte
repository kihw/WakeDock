<!--
  Service Form Component
  Reusable form for creating and editing Docker services
-->
<script lang="ts">
  import { createEventDispatcher, onMount } from 'svelte';
  import { writable, get } from 'svelte/store';
  import Button from '../atoms/Button.svelte';
  import Input from '../atoms/Input.svelte';
  import Textarea from './Textarea.svelte';
  import Select from './Select.svelte';
  import Icon from '../../Icon.svelte';
  import {
    validateServiceConfig,
    sanitizeInput,
    generateCSRFToken,
    verifyCSRFToken,
  } from '../../../utils/validation';
  import { manageFocus, announceToScreenReader } from '../../../utils/accessibility';
  import { colors } from '$lib/design-system/tokens';

  // Props
  export let mode: 'create' | 'edit' = 'create';
  export let initialData: Partial<ServiceFormData> = {};
  export let isLoading = false;
  export let errors: Record<string, string> = {};

  // Events
  const dispatch = createEventDispatcher<{
    submit: { data: ServiceFormData; csrfToken: string };
    cancel: void;
    validate: ServiceFormData;
  }>();

  // Service form data interface
  interface ServiceFormData {
    name: string;
    image: string;
    tag: string;
    description: string;
    ports: Array<{ host: number; container: number; protocol: 'tcp' | 'udp' }>;
    environment: Array<{ key: string; value: string; isSecret: boolean }>;
    volumes: Array<{ host: string; container: string; mode: 'rw' | 'ro' }>;
    networks: string[];
    restart: 'no' | 'always' | 'on-failure' | 'unless-stopped';
    cpuLimit: number;
    memoryLimit: number;
    replicas: number;
    healthCheck: {
      enabled: boolean;
      command: string;
      interval: number;
      timeout: number;
      retries: number;
    };
    labels: Array<{ key: string; value: string }>;
  }

  // Security state
  let csrfToken = '';
  let formElement: HTMLFormElement;

  // Form state
  let formData = writable<ServiceFormData>({
    name: '',
    image: '',
    tag: 'latest',
    description: '',
    ports: [],
    environment: [],
    volumes: [],
    networks: [],
    restart: 'unless-stopped',
    cpuLimit: 0,
    memoryLimit: 0,
    replicas: 1,
    healthCheck: {
      enabled: false,
      command: '',
      interval: 30,
      timeout: 10,
      retries: 3,
    },
    labels: [],
    ...initialData,
  });

  // Validation
  let validationErrors = writable<Record<string, string>>({});
  let isValid = writable(false);

  // Initialize security and accessibility features
  onMount(() => {
    csrfToken = generateCSRFToken();

    // Announce form mode to screen readers
    const modeText = mode === 'create' ? 'Create new service' : 'Edit service';
    announceToScreenReader(`${modeText} form loaded`);
  });

  // Options
  const restartPolicies = [
    { value: 'no', label: 'No restart' },
    { value: 'always', label: 'Always restart' },
    { value: 'on-failure', label: 'On failure' },
    { value: 'unless-stopped', label: 'Unless stopped' },
  ];

  const protocolOptions = [
    { value: 'tcp', label: 'TCP' },
    { value: 'udp', label: 'UDP' },
  ];

  const volumeModes = [
    { value: 'rw', label: 'Read/Write' },
    { value: 'ro', label: 'Read Only' },
  ];

  // Add/remove functions for arrays with security and accessibility
  function addPort() {
    formData.update((data) => ({
      ...data,
      ports: [...data.ports, { host: 0, container: 0, protocol: 'tcp' }],
    }));
  }

  function removePort(index: number) {
    formData.update((data) => ({
      ...data,
      ports: data.ports.filter((_, i) => i !== index),
    }));
  }

  function addEnvironment() {
    formData.update((data) => ({
      ...data,
      environment: [...data.environment, { key: '', value: '', isSecret: false }],
    }));
  }

  function removeEnvironment(index: number) {
    formData.update((data) => ({
      ...data,
      environment: data.environment.filter((_, i) => i !== index),
    }));
  }

  function addVolume() {
    formData.update((data) => ({
      ...data,
      volumes: [...data.volumes, { host: '', container: '', mode: 'rw' }],
    }));
  }

  function removeVolume(index: number) {
    formData.update((data) => ({
      ...data,
      volumes: data.volumes.filter((_, i) => i !== index),
    }));
  }

  function addLabel() {
    formData.update((data) => ({
      ...data,
      labels: [...data.labels, { key: '', value: '' }],
    }));
  }

  function removeLabel(index: number) {
    formData.update((data) => ({
      ...data,
      labels: data.labels.filter((_, i) => i !== index),
    }));
  }

  // Validation with security checks
  function validateForm() {
    const data = get(formData);

    // Sanitize all string inputs
    const sanitizedData = {
      ...data,
      name: sanitizeInput(data.name),
      image: sanitizeInput(data.image),
      tag: sanitizeInput(data.tag),
      description: sanitizeInput(data.description),
      environment: data.environment.map((env) => ({
        ...env,
        key: sanitizeInput(env.key),
        value: env.isSecret ? env.value : sanitizeInput(env.value), // Don't sanitize secrets
      })),
      volumes: data.volumes.map((vol) => ({
        ...vol,
        host: sanitizeInput(vol.host),
        container: sanitizeInput(vol.container),
      })),
      labels: data.labels.map((label) => ({
        ...label,
        key: sanitizeInput(label.key),
        value: sanitizeInput(label.value),
      })),
      healthCheck: {
        ...data.healthCheck,
        command: sanitizeInput(data.healthCheck.command),
      },
    };

    // Verify CSRF token
    if (!verifyCSRFToken(csrfToken)) {
      validationErrors.update((errors) => ({
        ...errors,
        general: 'Security token expired. Please refresh the page.',
      }));
      isValid.set(false);
      return false;
    }

    const validation = validateServiceConfig(sanitizedData);

    validationErrors.set(validation.errors || {});
    isValid.set(validation.isValid);

    // Update form data with sanitized values
    formData.set(sanitizedData);

    dispatch('validate', sanitizedData);

    // Announce validation results
    if (validation.isValid) {
      announceToScreenReader('Form validation passed');
    } else {
      const errorCount = Object.keys(validation.errors || {}).length;
      announceToScreenReader(`Form validation failed. ${errorCount} errors found.`);

      // Focus first error field
      const firstErrorField = Object.keys(validation.errors || {})[0];
      if (firstErrorField) {
        const errorElement = document.querySelector(
          `[name="${firstErrorField}"], [data-field="${firstErrorField}"]`
        );
        if (errorElement) {
          manageFocus(errorElement as HTMLElement);
        }
      }
    }

    return validation.isValid;
  }

  // Form submission with security
  function handleSubmit() {
    if (validateForm()) {
      const data = get(formData);
      dispatch('submit', { data, csrfToken });
      announceToScreenReader('Form submitted successfully');
    }
  }

  function handleCancel() {
    dispatch('cancel');
  }

  // Auto-validation on data change
  $: {
    if ($formData) {
      validateForm();
    }
  }
</script>

<form on:submit|preventDefault={handleSubmit} class="space-y-6">
  <!-- Basic Information -->
  <div class="bg-secondary-800 rounded-lg p-6">
    <h3 class="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
      <Icon name="info" class="w-5 h-5 text-primary-400" />
      <span>Basic Information</span>
    </h3>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-4">
      <Input
        id="service-name"
        label="Service Name"
        bind:value={$formData.name}
        placeholder="my-service"
        required
        error={$validationErrors.name}
        disabled={mode === 'edit'}
      />

      <Input
        id="docker-image"
        label="Docker Image"
        bind:value={$formData.image}
        placeholder="nginx"
        required
        error={$validationErrors.image}
      />

      <Input
        id="docker-tag"
        label="Tag"
        bind:value={$formData.tag}
        placeholder="latest"
        error={$validationErrors.tag}
      />

      <Select label="Restart Policy" bind:value={$formData.restart} options={restartPolicies} />
    </div>

    <div class="mt-4">
      <Textarea
        label="Description"
        bind:value={$formData.description}
        placeholder="Service description..."
        rows={3}
      />
    </div>
  </div>

  <!-- Port Mappings -->
  <div class="bg-secondary-800 rounded-lg p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-white flex items-center space-x-2">
        <Icon name="network" class="w-5 h-5 text-success-400" />
        <span>Port Mappings</span>
      </h3>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        on:click={addPort}
        class="flex items-center space-x-1"
      >
        <Icon name="plus" class="w-4 h-4" />
        <span>Add Port</span>
      </Button>
    </div>

    {#if $formData.ports.length === 0}
      <div class="text-center py-8 text-secondary-400">
        <Icon name="network" class="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No port mappings configured</p>
        <p class="text-sm">Click "Add Port" to expose service ports</p>
      </div>
    {:else}
      <div class="space-y-3">
        {#each $formData.ports as port, index}
          <div class="flex items-center space-x-3 p-3 bg-secondary-700 rounded-lg">
            <Input
              type="number"
              placeholder="Host port"
              bind:value={port.host}
              class="flex-1"
              min={1}
              max={65535}
              label=""
              id="host-port-{index}"
            />
            <Icon name="arrow-right" class="w-4 h-4 text-secondary-400" />
            <Input
              type="number"
              placeholder="Container port"
              bind:value={port.container}
              class="flex-1"
              min={1}
              max={65535}
              label=""
              id="container-port-{index}"
            />
            <Select bind:value={port.protocol} options={protocolOptions} class="w-20" label="" />
            <Button type="button" variant="danger" size="sm" on:click={() => removePort(index)}>
              <Icon name="trash-2" class="w-4 h-4" />
            </Button>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Environment Variables -->
  <div class="bg-secondary-800 rounded-lg p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-white flex items-center space-x-2">
        <Icon name="settings" class="w-5 h-5 text-warning-400" />
        <span>Environment Variables</span>
      </h3>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        on:click={addEnvironment}
        class="flex items-center space-x-1"
      >
        <Icon name="plus" class="w-4 h-4" />
        <span>Add Variable</span>
      </Button>
    </div>

    {#if $formData.environment.length === 0}
      <div class="text-center py-8 text-secondary-400">
        <Icon name="settings" class="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No environment variables configured</p>
      </div>
    {:else}
      <div class="space-y-3">
        {#each $formData.environment as env, index}
          <div class="flex items-center space-x-3 p-3 bg-secondary-700 rounded-lg">
            <Input
              id="env-key-{index}"
              placeholder="Variable name"
              bind:value={env.key}
              class="flex-1"
              label=""
            />
            <Icon name="equal" class="w-4 h-4 text-secondary-400" />
            <Input
              id="env-value-{index}"
              type={env.isSecret ? 'password' : 'text'}
              placeholder="Value"
              bind:value={env.value}
              class="flex-1"
              label=""
            />
            <label class="flex items-center space-x-2 text-sm text-secondary-300">
              <input
                type="checkbox"
                bind:checked={env.isSecret}
                class="rounded border-secondary-600 bg-secondary-700 text-primary-600"
              />
              <span>Secret</span>
            </label>
            <Button
              type="button"
              variant="danger"
              size="sm"
              on:click={() => removeEnvironment(index)}
            >
              <Icon name="trash-2" class="w-4 h-4" />
            </Button>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Volume Mounts -->
  <div class="bg-secondary-800 rounded-lg p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-white flex items-center space-x-2">
        <Icon name="hard-drive" class="w-5 h-5 text-purple-400" />
        <span>Volume Mounts</span>
      </h3>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        on:click={addVolume}
        class="flex items-center space-x-1"
      >
        <Icon name="plus" class="w-4 h-4" />
        <span>Add Volume</span>
      </Button>
    </div>

    {#if $formData.volumes.length === 0}
      <div class="text-center py-8 text-secondary-400">
        <Icon name="hard-drive" class="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No volume mounts configured</p>
      </div>
    {:else}
      <div class="space-y-3">
        {#each $formData.volumes as volume, index}
          <div class="flex items-center space-x-3 p-3 bg-secondary-700 rounded-lg">
            <Input
              id="volume-host-{index}"
              placeholder="Host path"
              bind:value={volume.host}
              class="flex-1"
              label=""
            />
            <Icon name="arrow-right" class="w-4 h-4 text-secondary-400" />
            <Input
              id="volume-container-{index}"
              placeholder="Container path"
              bind:value={volume.container}
              class="flex-1"
              label=""
            />
            <Select bind:value={volume.mode} options={volumeModes} class="w-24" label="" />
            <Button type="button" variant="danger" size="sm" on:click={() => removeVolume(index)}>
              <Icon name="trash-2" class="w-4 h-4" />
            </Button>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Resource Limits -->
  <div class="bg-secondary-800 rounded-lg p-6">
    <h3 class="text-lg font-semibold text-white mb-4 flex items-center space-x-2">
      <Icon name="cpu" class="w-5 h-5 text-error-400" />
      <span>Resource Limits</span>
    </h3>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <Input
        type="number"
        label="CPU Limit (cores)"
        bind:value={$formData.cpuLimit}
        placeholder="0 = unlimited"
        min={0}
        step={0.1}
        id="cpu-limit"
      />

      <Input
        type="number"
        label="Memory Limit (MB)"
        bind:value={$formData.memoryLimit}
        placeholder="0 = unlimited"
        min={0}
        id="memory-limit"
      />

      <Input type="number" id="replicas" label="Replicas" bind:value={$formData.replicas} min={1} />
    </div>
  </div>

  <!-- Health Check -->
  <div class="bg-secondary-800 rounded-lg p-6">
    <div class="flex items-center space-x-2 mb-4">
      <input
        type="checkbox"
        bind:checked={$formData.healthCheck.enabled}
        class="rounded border-secondary-600 bg-secondary-700 text-primary-600"
      />
      <h3 class="text-lg font-semibold text-white flex items-center space-x-2">
        <Icon name="heart" class="w-5 h-5 text-pink-400" />
        <span>Health Check</span>
      </h3>
    </div>

    {#if $formData.healthCheck.enabled}
      <div class="space-y-4">
        <Input
          id="health-check-command"
          label="Health Check Command"
          bind:value={$formData.healthCheck.command}
          placeholder="curl -f http://localhost:8080/health"
        />

        <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Input
            type="number"
            label="Interval (seconds)"
            bind:value={$formData.healthCheck.interval}
            min={1}
            id="health-interval"
          />

          <Input
            type="number"
            label="Timeout (seconds)"
            bind:value={$formData.healthCheck.timeout}
            min={1}
            id="health-timeout"
          />

          <Input
            type="number"
            id="retries"
            label="Retries"
            bind:value={$formData.healthCheck.retries}
            min={1}
          />
        </div>
      </div>
    {/if}
  </div>

  <!-- Labels -->
  <div class="bg-secondary-800 rounded-lg p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="text-lg font-semibold text-white flex items-center space-x-2">
        <Icon name="tag" class="w-5 h-5 text-indigo-400" />
        <span>Labels</span>
      </h3>
      <Button
        type="button"
        variant="secondary"
        size="sm"
        on:click={addLabel}
        class="flex items-center space-x-1"
      >
        <Icon name="plus" class="w-4 h-4" />
        <span>Add Label</span>
      </Button>
    </div>

    {#if $formData.labels.length === 0}
      <div class="text-center py-8 text-secondary-400">
        <Icon name="tag" class="w-12 h-12 mx-auto mb-2 opacity-50" />
        <p>No labels configured</p>
      </div>
    {:else}
      <div class="space-y-3">
        {#each $formData.labels as label, index}
          <div class="flex items-center space-x-3 p-3 bg-secondary-700 rounded-lg">
            <Input
              id="label-key-{index}"
              placeholder="Label key"
              bind:value={label.key}
              class="flex-1"
              label=""
            />
            <Icon name="equal" class="w-4 h-4 text-secondary-400" />
            <Input
              id="label-value-{index}"
              placeholder="Label value"
              bind:value={label.value}
              class="flex-1"
              label=""
            />
            <Button type="button" variant="danger" size="sm" on:click={() => removeLabel(index)}>
              <Icon name="trash-2" class="w-4 h-4" />
            </Button>
          </div>
        {/each}
      </div>
    {/if}
  </div>

  <!-- Form Actions -->
  <div class="flex items-center justify-end space-x-3 pt-6 border-t border-secondary-700">
    <Button type="button" variant="secondary" on:click={handleCancel} disabled={isLoading}>
      Cancel
    </Button>

    <Button
      type="submit"
      variant="primary"
      disabled={!$isValid || isLoading}
      loading={isLoading}
      class="min-w-32"
    >
      {mode === 'create' ? 'Create Service' : 'Update Service'}
    </Button>
  </div>
</form>
