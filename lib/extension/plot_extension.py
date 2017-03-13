

def cw_postprocess(f, a, summary):
    y_data = a.lines[0].get_ydata()
    if min(y_data) > 0 and max(y_data) > min(y_data) * 100:
        a.set_yscale('log')
