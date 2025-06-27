<script lang="ts">
    import { onMount, onDestroy } from "svelte";
    import { scaleLinear, scaleTime } from "d3-scale";
    import { line, curveMonotoneX } from "d3-shape";
    import { max, extent } from "d3-array";

    export let data: Array<{ timestamp: Date; value: number }> = [];
    export let width = 400;
    export let height = 200;
    export let color = "#3b82f6";
    export let strokeWidth = 2;
    export let showDots = true;
    export let animate = true;
    export let yAxisLabel = "";
    export let xAxisLabel = "";
    export let formatValue = (value: number) => value.toFixed(1);
    export let formatTime = (date: Date) => date.toLocaleTimeString();

    let svgElement: SVGElement;
    let pathElement: SVGPathElement;

    const margin = { top: 20, right: 30, bottom: 40, left: 50 };
    $: innerWidth = width - margin.left - margin.right;
    $: innerHeight = height - margin.top - margin.bottom;

    $: xScale = scaleTime()
        .domain(extent(data, (d) => d.timestamp) as [Date, Date])
        .range([0, innerWidth]);

    $: yScale = scaleLinear()
        .domain([0, max(data, (d) => d.value) || 100])
        .nice()
        .range([innerHeight, 0]);

    $: lineGenerator = line<{ timestamp: Date; value: number }>()
        .x((d) => xScale(d.timestamp))
        .y((d) => yScale(d.value))
        .curve(curveMonotoneX);

    $: pathData = lineGenerator(data) || "";

    $: yTicks = yScale.ticks(5);
    $: xTicks = xScale.ticks(5);

    onMount(() => {
        if (animate && pathElement) {
            const length = pathElement.getTotalLength();
            pathElement.style.strokeDasharray = `${length} ${length}`;
            pathElement.style.strokeDashoffset = `${length}`;
            pathElement.animate(
                [{ strokeDashoffset: length }, { strokeDashoffset: 0 }],
                {
                    duration: 1000,
                    easing: "ease-out",
                },
            );
        }
    });

    $: if (pathElement && animate) {
        const length = pathElement.getTotalLength();
        pathElement.style.strokeDasharray = `${length} ${length}`;
        pathElement.style.strokeDashoffset = `${length}`;
        pathElement.animate(
            [{ strokeDashoffset: length }, { strokeDashoffset: 0 }],
            {
                duration: 500,
                easing: "ease-out",
            },
        );
    }
</script>

<div class="chart-container">
    <svg bind:this={svgElement} {width} {height} class="line-chart">
        <defs>
            <linearGradient
                id="gradient-{color.replace('#', '')}"
                x1="0%"
                y1="0%"
                x2="0%"
                y2="100%"
            >
                <stop offset="0%" style="stop-color:{color};stop-opacity:0.3" />
                <stop
                    offset="100%"
                    style="stop-color:{color};stop-opacity:0.1"
                />
            </linearGradient>
        </defs>

        <g transform="translate({margin.left}, {margin.top})">
            <!-- Grid lines -->
            <g class="grid">
                {#each yTicks as tick}
                    <line
                        x1="0"
                        y1={yScale(tick)}
                        x2={innerWidth}
                        y2={yScale(tick)}
                        stroke="#e5e7eb"
                        stroke-dasharray="2,2"
                    />
                {/each}
                {#each xTicks as tick}
                    <line
                        x1={xScale(tick)}
                        y1="0"
                        x2={xScale(tick)}
                        y2={innerHeight}
                        stroke="#e5e7eb"
                        stroke-dasharray="2,2"
                    />
                {/each}
            </g>

            <!-- Area under the line -->
            {#if data.length > 0}
                <path
                    d="{lineGenerator(data)}L{xScale(
                        data[data.length - 1].timestamp,
                    )},{innerHeight}L{xScale(data[0].timestamp)},{innerHeight}Z"
                    fill="url(#gradient-{color.replace('#', '')})"
                />
            {/if}

            <!-- Line -->
            {#if data.length > 0}
                <path
                    bind:this={pathElement}
                    d={pathData}
                    fill="none"
                    stroke={color}
                    stroke-width={strokeWidth}
                    stroke-linecap="round"
                    stroke-linejoin="round"
                />
            {/if}

            <!-- Data points -->
            {#if showDots}
                {#each data as point}
                    <circle
                        cx={xScale(point.timestamp)}
                        cy={yScale(point.value)}
                        r="3"
                        fill={color}
                        stroke="white"
                        stroke-width="2"
                        class="data-point"
                    >
                        <title
                            >{formatTime(point.timestamp)}: {formatValue(
                                point.value,
                            )}</title
                        >
                    </circle>
                {/each}
            {/if}

            <!-- Y-axis -->
            <g class="y-axis">
                <line x1="0" y1="0" x2="0" y2={innerHeight} stroke="#374151" />
                {#each yTicks as tick}
                    <g transform="translate(0, {yScale(tick)})">
                        <line x1="0" y1="0" x2="-5" y2="0" stroke="#374151" />
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
                {#if yAxisLabel}
                    <text
                        x={-innerHeight / 2}
                        y="-35"
                        transform="rotate(-90, {-innerHeight / 2}, -35)"
                        text-anchor="middle"
                        class="axis-title"
                    >
                        {yAxisLabel}
                    </text>
                {/if}
            </g>

            <!-- X-axis -->
            <g class="x-axis" transform="translate(0, {innerHeight})">
                <line x1="0" y1="0" x2={innerWidth} y2="0" stroke="#374151" />
                {#each xTicks as tick}
                    <g transform="translate({xScale(tick)}, 0)">
                        <line x1="0" y1="0" x2="0" y2="5" stroke="#374151" />
                        <text
                            x="0"
                            y="8"
                            dy="0.71em"
                            text-anchor="middle"
                            class="axis-label"
                        >
                            {formatTime(tick)}
                        </text>
                    </g>
                {/each}
                {#if xAxisLabel}
                    <text
                        x={innerWidth / 2}
                        y="35"
                        text-anchor="middle"
                        class="axis-title"
                    >
                        {xAxisLabel}
                    </text>
                {/if}
            </g>
        </g>
    </svg>
</div>

<style>
    .chart-container {
        position: relative;
        overflow: visible;
    }

    .line-chart {
        background: white;
        border-radius: 8px;
    }

    .data-point {
        cursor: pointer;
        transition: r 0.2s ease;
    }

    .data-point:hover {
        r: 5;
    }

    .axis-label {
        font-size: 12px;
        fill: #6b7280;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            sans-serif;
    }

    .axis-title {
        font-size: 14px;
        fill: #374151;
        font-weight: 500;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
            sans-serif;
    }

    .grid line {
        opacity: 0.5;
    }
</style>
