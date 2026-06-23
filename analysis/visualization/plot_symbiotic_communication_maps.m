clc;
clear;
close all;

script_dir = fileparts(mfilename('fullpath'));
repo_root = fileparts(fileparts(script_dir));

n_color = 256;
base_jet = jet(n_color);
soft_factor = 0.5;     
white_mix   = 1.0 - soft_factor;
cmap_cool = base_jet * soft_factor + white_mix * ones(size(base_jet));

file_noris = fullfile(repo_root, 'data', 'power_maps', 'scene3_noris.json');
file_0 = fullfile(repo_root, 'data', 'power_maps', 'scene3_0.json');
file_1 = fullfile(repo_root, 'data', 'power_maps', 'scene3_1.json');

step_size = 0.1;
max_z_jump = 0.4;

disp('Reading the three JSON files...');
data_noris = jsondecode(fileread(file_noris));
data_0     = jsondecode(fileread(file_0));
data_1     = jsondecode(fileread(file_1));

x_noris = [data_noris.x]'; y_noris = [data_noris.y]'; z_noris = [data_noris.z]' - 0.4; p_noris = [data_noris.power]';
x_0 = [data_0.x]';         y_0 = [data_0.y]';         z_0 = [data_0.z]' - 0.4;         p_0 = [data_0.power]';
x_1 = [data_1.x]';         y_1 = [data_1.y]';         z_1 = [data_1.z]' - 0.4;         p_1 = [data_1.power]';

disp('Reconstructing the power grids...');
min_x = min([x_noris; x_0; x_1]);
min_y = min([y_noris; y_0; y_1]);

c_idx_noris = round((x_noris - min_x) / step_size) + 1;
r_idx_noris = round((y_noris - min_y) / step_size) + 1;
c_idx_0 = round((x_0 - min_x) / step_size) + 1;
r_idx_0 = round((y_0 - min_y) / step_size) + 1;
c_idx_1 = round((x_1 - min_x) / step_size) + 1;
r_idx_1 = round((y_1 - min_y) / step_size) + 1;

max_c = max([c_idx_noris; c_idx_0; c_idx_1]);
max_r = max([r_idx_noris; r_idx_0; r_idx_1]);

X_vec = min_x + (0 : max_c - 1) * step_size;
Y_vec = min_y + (0 : max_r - 1) * step_size;
[Xg, Yg] = meshgrid(X_vec, Y_vec);

Z_map_noris = nan(max_r, max_c); P_map_noris = nan(max_r, max_c);
Z_map_0     = nan(max_r, max_c); P_map_0     = nan(max_r, max_c);
Z_map_1     = nan(max_r, max_c); P_map_1     = nan(max_r, max_c);

for i = 1:length(x_noris)
    Z_map_noris(r_idx_noris(i), c_idx_noris(i)) = z_noris(i);
    P_map_noris(r_idx_noris(i), c_idx_noris(i)) = p_noris(i);
end
for i = 1:length(x_0)
    Z_map_0(r_idx_0(i), c_idx_0(i)) = z_0(i);
    P_map_0(r_idx_0(i), c_idx_0(i)) = p_0(i);
end
for i = 1:length(x_1)
    Z_map_1(r_idx_1(i), c_idx_1(i)) = z_1(i);
    P_map_1(r_idx_1(i), c_idx_1(i)) = p_1(i);
end

disp('Rendering the power maps...');

fig1 = figure('Name', 'Top-Down Power Map: Scene 3 No RIS', 'Color', 'w', 'Position', [50, 100, 500, 600]);
hold on; axis equal tight; axis off; view(0, 90);
plot_split_surf(Xg, Yg, Z_map_noris, Z_map_noris, P_map_noris, max_z_jump);
colormap(cmap_cool); clim([-80 -30]); 
set(gca, 'Position', [0 0 1 1]); camzoom(1.1);
title('Scene 3: No RIS', 'Units', 'normalized', 'Position', [0.5, 0.95, 0], 'FontSize', 14);

fig2 = figure('Name', 'Top-Down Power Map: Scene 3_0', 'Color', 'w', 'Position', [600, 100, 500, 600]);
hold on; axis equal tight; axis off; view(0, 90);
plot_split_surf(Xg, Yg, Z_map_0, Z_map_0, P_map_0, max_z_jump);
colormap(cmap_cool); clim([-80 -30]); 
set(gca, 'Position', [0 0 1 1]); camzoom(1.1);
title('Scene 3: 0', 'Units', 'normalized', 'Position', [0.5, 0.95, 0], 'FontSize', 14);

fig3 = figure('Name', 'Top-Down Power Map: Scene 3_1', 'Color', 'w', 'Position', [1150, 100, 500, 600]);
hold on; axis equal tight; axis off; view(0, 90);
plot_split_surf(Xg, Yg, Z_map_1, Z_map_1, P_map_1, max_z_jump);
colormap(cmap_cool); clim([-80 -30]); 
set(gca, 'Position', [0 0 1 1]); camzoom(1.1);
title('Scene 3: 1', 'Units', 'normalized', 'Position', [0.5, 0.95, 0], 'FontSize', 14);

function p = plot_split_surf(X, Y, Z_logic, Z_draw, C, max_jump)
    [nr, nc] = size(X);
    V = [X(:), Y(:), Z_draw(:)];
    
    [R, C_idx] = ndgrid(1:nr-1, 1:nc-1);
    idx1 = R + (C_idx-1)*nr;
    idx2 = R+1 + (C_idx-1)*nr;
    idx3 = R+1 + C_idx*nr;
    idx4 = R + C_idx*nr;
    F = [idx1(:), idx2(:), idx3(:), idx4(:)];
    
    v1_z = Z_logic(idx1(:)); v2_z = Z_logic(idx2(:));
    v3_z = Z_logic(idx3(:)); v4_z = Z_logic(idx4(:));
    
    valid_z = ~isnan(v1_z) & ~isnan(v2_z) & ~isnan(v3_z) & ~isnan(v4_z);
    max_z = max([v1_z, v2_z, v3_z, v4_z], [], 2);
    min_z = min([v1_z, v2_z, v3_z, v4_z], [], 2);
    valid_faces = valid_z & ((max_z - min_z) <= max_jump);
    
    F = F(valid_faces, :);
    p = patch('Vertices', V, 'Faces', F, 'FaceVertexCData', C(:), ...
          'FaceColor', 'interp', 'EdgeColor', 'none', 'FaceAlpha', 1.0); 
end
