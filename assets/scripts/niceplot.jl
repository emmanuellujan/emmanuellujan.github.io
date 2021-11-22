using Plots
default(legend = false)
x = y = range(-5, 5, length = 40)
n = 200
anim = @animate for i in range(0, stop = 4π, length = n)
    f(x, y) = sin(x + 10sin(i)) + cos(y)
    p = plot(x, y, f, st = :surface, alpha = 0.4, c = :Reds_9,
             xlabel = "Software Engineering, HPC",
             ylabel = "AI, ML",
             zlabel = "Computer Science, Computational Science")
end
gif(anim, "niceplot.gif", fps = 15)
