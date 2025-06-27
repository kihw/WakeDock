<script lang="ts">
    import { onMount } from "svelte";
    import { scaleBand, scaleLinear } from "d3-scale";
    import { max } from "d3-array";

    export let data: Array<{ label: string; value: number; color?: string }> =
        [];
    export let width = 400;
    export let height = 300;
    export let color = "#3b82f6";
    export let animate = true;
    export let horizontal = false;
    export let showValues = true;
    export let showGrid = true;
    export let formatValue = (value: number) => value.toString();
    export let formatLabel = (label: string) => label;

    let mounted = false;
    let bars: HTMLElement[] = [];

    const margin = { top: 20, right: 30, bottom: 60, left: 80 };
    $: innerWidth = width - margin.left - margin.right;
    $: innerHeight = height - margin.top - margin.bottom;

    $: maxValue = max(data, (d) => d.value) || 100;

    $: xScale = horizontal
        ? scaleLinear().domain([0, maxValue]).range([0, innerWidth])
        : scaleBand()
              .domain(data.map((d) => d.label))
              .range([0, innerWidth])
              .padding(0.1);

    $: yScale = horizontal
        ? scaleBand()
              .domain(data.map((d) => d.label))
              .range([0, innerHeight])
              .padding(0.1)
        : scaleLinear().domain([0, maxValue]).range([innerHeight, 0]);

    $: ticks = horizontal ? (xScale as any).ticks(5) : (yScale as any).ticks(5);

    onMount(() => {
        mounted = true;
        if (animate) {
            bars.forEach((bar, index) => {
                if (bar) {
                    bar.style.animationDelay = `${index * 100}ms`;
                }
            });
        }
    });

    function getBarProps(item: any, index: number) {
        if (horizontal) {
            return {
                x: 0,
                y: yScale(item.label),
                width: xScale(item.value),
                height: yScale.bandwidth(),
                color: item.color || color,
            };
        } else {
            return {
                x: xScale(item.label),
                y: yScale(item.value),
                width: xScale.bandwidth(),
                height: innerHeight - yScale(item.value),
                color: item.color || color,
            };
        }
    }

    function getValueTextProps(item: any, index: number) {
        const barProps = getBarProps(item, index);
        if (horizontal) {
            return {
                x: barProps.width + 5,
                y: barProps.y + barProps.height / 2,
                textAnchor: "start",
                dy: "0.35em",
            };
        } else {
            return {
                x: barProps.x + barProps.width / 2,
                y: barProps.y - 5,
                textAnchor: "middle",
                dy: "0",
            };
        }
    }
</script>

<div class="bar-chart-container">
    <svg {width} {height} class="bar-chart">
        <g transform="translate({margin.left}, {margin.top})">
            <!-- Grid lines -->
            {#if showGrid}
                <g class="grid">
                    {#if horizontal}
                        {#each ticks as tick}
                            <line
                                x1={xScale(tick)}
                                y1="0"
                                x2={xScale(tick)}
                                y2={innerHeight}
                                stroke="#e5e7eb"
                                stroke-dasharray="2,2"
                            />
                        {/each}
                    {:else}
                        {#each ticks as tick}
                            <line
                                x1="0"
                                y1={yScale(tick)}
                                x2={innerWidth}
                                y2={yScale(tick)}
                                stroke="#e5e7eb"
                                stroke-dasharray="2,2"
                            />
                        {/each}
                    {/if}
                </g>
            {/if}

            <!-- Bars -->
            <g class="bars">
                {#each data as item, index}
                    {@const barProps = getBarProps(item, index)}
                    <rect
                        bind:this={bars[index]}
                        x={barProps.x}
                        y={barProps.y}
                        width={barProps.width}
                        height={barProps.height}
                        fill={barProps.color}
                        class="bar {animate ? 'animated' : ''}"
                        stroke="none"
                        rx="3"
                        ry="3"
                    >
                        <title
                            >{formatLabel(item.label)}: {formatValue(
                                item.value,
                            )}</title
                        >
                    </rect>

                    {#if showValues}
                        {@const textProps = getValueTextProps(item, index)}
                        <text
                            x={textProps.x}
                            y={textProps.y}
                            text-anchor={textProps.textAnchor}
                            dy={textProps.dy}
                            class="value-label"
                        >
                            {formatValue(item.value)}
                        </text>
                    {/if}
                {/each}
            </g>

            <!-- Axes -->
            {#if horizontal}
                <!-- X-axis (horizontal) -->
                <g class="x-axis" transform="translate(0, {innerHeight})">
                    <line
                        x1="0"
                        y1="0"
                        x2={innerWidth}
                        y2="0"
                        stroke="#374151"
                    />
                    {#each ticks as tick}
                        <g transform="translate({xScale(tick)}, 0)">
                            <line
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="5"
                                stroke="#374151"
                            />
                            <text
                                x="0"
                                y="8"
                                dy="0.71em"
                                text-anchor="middle"
                                class="axis-label"
                            >
                                {formatValue(tick)}
                            </text>
                        </g>
                    {/each}
                </g>

                <!-- Y-axis (horizontal) -->
                <g class="y-axis">
                    <line
                        x1="0"
                        y1="0"
                        x2="0"
                        y2={innerHeight}
                        stroke="#374151"
                    />
                    {#each data as item}
                        <g
                            transform="translate(0, {yScale(item.label) +
                                yScale.bandwidth() / 2})"
                        >
                            <line
                                x1="0"
                                y1="0"
                                x2="-5"
                                y2="0"
                                stroke="#374151"
                            />
                            <text
                                x="-8"
                                y="0"
                                dy="0.35em"
                                text-anchor="end"
                                class="axis-label"
                            >
                                {formatLabel(item.label)}
                            </text>
                        </g>
                    {/each}
                </g>
            {:else}
                <!-- X-axis (vertical) -->
                <g class="x-axis" transform="translate(0, {innerHeight})">
                    <line
                        x1="0"
                        y1="0"
                        x2={innerWidth}
                        y2="0"
                        stroke="#374151"
                    />
                    {#each data as item}
                        <g
                            transform="translate({xScale(item.label) +
                                xScale.bandwidth() / 2}, 0)"
                        >
                            <line
                                x1="0"
                                y1="0"
                                x2="0"
                                y2="5"
                                stroke="#374151"
                            />
                            <text
                                x="0"
                                y="8"
                                dy="0.71em"
                                text-anchor="middle"
                                class="axis-label"
                                transform="rotate(-45, 0, 8)"
                            >
                                {formatLabel(item.label)}
                            </text>
                        </g>
                    {/each}
                </g>

                <!-- Y-axis (vertical) -->
                <g class="y-axis">
                    <line
                        x1="0"
                        y1="0"
                        x2="0"
                        y2={innerHeight}
                        stroke="#374151"
                    />
                    {#each ticks as tick}
                        <g transform="translate(0, {yScale(tick)})">
                            <line
                                x1="0"
                                y1="0"
                                x2="-5"
                                y2="0"
                                stroke="#374151"
                            />
                            <text
                                x="-8"
                                y="0"
                                dy="0.35em"
                                text-anchor="end"
                                class="axis-label"
                            >
                                {formatValue(tick)}
                            </text>
                        </g>
                    {/each}
                </g>
            {/if}
        </g>
    </svg>
</div>

<style>
    .bar-chart-container {
        position: relative;
        overflow: visible;
    }

    .bar-chart {
        background: white;
        border-radius: 8px;
    }

    .bar {
        cursor: pointer;
        transition: opacity 0.2s ease;
    }

    .bar:hover {
        opacity: 0.8;
    }

    .bar.animated {
        animation: growBar 0.6s ease-out forwards;
        transform-origin: bottom;
    }

    @keyframes growBar {
        from {
            transform: scaleY(0);
        }
        to {
            transform: scaleY(1);
        }
    }

    .value-label {
        font-size: 12px;
        font-weight: 500;
        fill: #374151;
        pointer-events: none;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            sans-serif;
    }

    .axis-label {
        font-size: 12px;
        fill: #6b7280;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            sans-serif;
    }

    .grid line {
        opacity: 0.5;
    }
</style>
