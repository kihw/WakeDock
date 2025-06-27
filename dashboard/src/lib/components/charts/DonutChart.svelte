<script lang="ts">
    import { onMount } from "svelte";
    import { arc, pie } from "d3-shape";
    import { scaleOrdinal } from "d3-scale";

    export let data: Array<{ label: string; value: number; color?: string }> =
        [];
    export let size = 200;
    export let innerRadius = 60;
    export let colors = [
        "#3b82f6",
        "#ef4444",
        "#10b981",
        "#f59e0b",
        "#8b5cf6",
        "#f97316",
    ];
    export let animate = true;
    export let showLabels = true;
    export let showLegend = true;
    export let centerText = "";
    export let centerValue = "";
    export let formatValue = (value: number) => value.toString();
    export let formatPercent = (value: number, total: number) =>
        `${((value / total) * 100).toFixed(1)}%`;

    let svgElement: SVGElement;
    let mounted = false;

    const radius = size / 2;
    const outerRadius = radius - 10;

    $: colorScale = scaleOrdinal<string>()
        .domain(data.map((d) => d.label))
        .range(colors);

    $: total = data.reduce((sum, d) => sum + d.value, 0);

    $: pieGenerator = pie<{ label: string; value: number; color?: string }>()
        .value((d) => d.value)
        .sort(null);

    $: arcGenerator = arc().innerRadius(innerRadius).outerRadius(outerRadius);

    $: labelArcGenerator = arc()
        .innerRadius(outerRadius + 10)
        .outerRadius(outerRadius + 10);

    $: arcs = pieGenerator(data);

    onMount(() => {
        mounted = true;
    });

    function getArcPath(d: any, animationProgress = 1) {
        const arcData = {
            ...d,
            endAngle:
                d.startAngle + (d.endAngle - d.startAngle) * animationProgress,
        };
        return arcGenerator(arcData);
    }

    function getLabelPosition(d: any) {
        const [x, y] = labelArcGenerator.centroid(d);
        return { x, y };
    }

    function getSliceColor(d: any, index: number) {
        return d.data.color || colorScale(d.data.label);
    }
</script>

<div class="donut-chart-container">
    <div class="chart-wrapper">
        <svg
            bind:this={svgElement}
            width={size}
            height={size}
            class="donut-chart"
        >
            <g transform="translate({radius}, {radius})">
                {#each arcs as arc, index}
                    <g class="arc-group">
                        <path
                            d={getArcPath(arc, mounted && animate ? 1 : 0)}
                            fill={getSliceColor(arc, index)}
                            stroke="white"
                            stroke-width="2"
                            class="arc-path"
                            style="transition: {animate
                                ? 'all 0.3s ease'
                                : 'none'}"
                        >
                            <title
                                >{arc.data.label}: {formatValue(arc.data.value)}
                                ({formatPercent(arc.data.value, total)})</title
                            >
                        </path>

                        {#if showLabels && arc.data.value > 0}
                            {@const labelPos = getLabelPosition(arc)}
                            {@const percent = (arc.data.value / total) * 100}
                            {#if percent > 5}
                                <text
                                    x={labelPos.x}
                                    y={labelPos.y}
                                    text-anchor="middle"
                                    class="arc-label"
                                    dy="0.35em"
                                >
                                    {formatPercent(arc.data.value, total)}
                                </text>
                            {/if}
                        {/if}
                    </g>
                {/each}

                <!-- Center text -->
                {#if centerText || centerValue}
                    <g class="center-text">
                        {#if centerValue}
                            <text
                                x="0"
                                y={centerText ? "-8" : "0"}
                                text-anchor="middle"
                                class="center-value"
                                dy="0.35em"
                            >
                                {centerValue}
                            </text>
                        {/if}
                        {#if centerText}
                            <text
                                x="0"
                                y={centerValue ? "12" : "0"}
                                text-anchor="middle"
                                class="center-label"
                                dy="0.35em"
                            >
                                {centerText}
                            </text>
                        {/if}
                    </g>
                {/if}
            </g>
        </svg>
    </div>

    {#if showLegend && data.length > 0}
        <div class="legend">
            {#each data as item, index}
                <div class="legend-item">
                    <div
                        class="legend-color"
                        style="background-color: {getSliceColor(
                            { data: item },
                            index,
                        )}"
                    ></div>
                    <span class="legend-label">{item.label}</span>
                    <span class="legend-value">{formatValue(item.value)}</span>
                </div>
            {/each}
        </div>
    {/if}
</div>

<style>
    .donut-chart-container {
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 1rem;
    }

    .chart-wrapper {
        position: relative;
    }

    .donut-chart {
        background: white;
        border-radius: 8px;
    }

    .arc-path {
        cursor: pointer;
        transition: opacity 0.2s ease;
    }

    .arc-path:hover {
        opacity: 0.8;
    }

    .arc-label {
        font-size: 12px;
        font-weight: 500;
        fill: white;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
        pointer-events: none;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            sans-serif;
    }

    .center-value {
        font-size: 24px;
        font-weight: bold;
        fill: #1f2937;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            sans-serif;
    }

    .center-label {
        font-size: 14px;
        fill: #6b7280;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            sans-serif;
    }

    .legend {
        display: flex;
        flex-direction: column;
        gap: 0.5rem;
        max-width: 300px;
        width: 100%;
    }

    .legend-item {
        display: flex;
        align-items: center;
        gap: 0.5rem;
        padding: 0.25rem 0;
    }

    .legend-color {
        width: 12px;
        height: 12px;
        border-radius: 2px;
        flex-shrink: 0;
    }

    .legend-label {
        flex: 1;
        font-size: 14px;
        color: #374151;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            sans-serif;
    }

    .legend-value {
        font-size: 14px;
        font-weight: 500;
        color: #1f2937;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            sans-serif;
    }

    @media (min-width: 768px) {
        .donut-chart-container {
            flex-direction: row;
            align-items: flex-start;
        }

        .legend {
            max-width: 200px;
        }
    }
</style>
