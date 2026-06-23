%-------------------------------------------------
%-------------------------------------------------

function [metrix,metrix_inv] = Creat_metrix(num_x,num_y,p,lambda,distance,mode_select,dis)
	X_lable_max=(num_x-1) * p/2;
	Y_lable_max=(num_y-1) * p/2;
    
    X_lable= - X_lable_max: p : X_lable_max;
    Y_lable= -Y_lable_max:p:Y_lable_max;
	index = 1;
	total_unit_num = num_x * num_y;
	lable=zeros(total_unit_num,2);

	for i=1:num_x
		for j=1:num_y
            if dis == 0
                lable(index,:) = [X_lable(i),Y_lable(j)];
            end
            index = index +1;
		end
	end 
	
	
	dis_r=zeros(total_unit_num,total_unit_num);
	%phi=zeros(total_unit_num,total_unit_num);%OAM
    
   for m=1:total_unit_num
        for k=1:total_unit_num
			dis_r(m,k) = sqrt(distance^2+ (lable(m,1) - lable(k,1))^2 + (lable(m,2) - lable(k,2))^2);
        end
   end 
    
	k = 2*pi/lambda; 
    
	if mode_select == 0
        metrix = exp((-1i*k).*dis_r);
        metrix_inv = exp((1i*k).*dis_r);
        %metrix = exp((-1i*k).*dis_r+li*OAM_mode*phi);
        %metrix_inv = exp((1i*k).*dis_r-li*OAM_mode*phi);
    else
        metrix = exp((-1i*k).*dis_r)./dis_r;
        metrix_inv = exp((1i*k).*dis_r)./dis_r./dis_r;
	end
end
