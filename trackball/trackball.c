#include <math.h>

struct vector3 {
  float x, y, z;
};

struct tracked_object {
  float width;
  float height;
};

struct trackball {
  struct tracked_object tr_obj;

  // Normalized
  struct vector3 mouse_old;
  struct vector3 mouse_pos;

  struct vector3 rot_axis;
  float rot_ang;

  float radius;
};


// x, y tracked object
void trackball_proyect_mouse(struct trackball *tb, int x, int y) {

  float n;

  tb->mouse_pos.x = x - tb->tr_obj.width / 2.0;
  tb->mouse_pos.y = tb->tr_obj.height / 2.0 - y;
  tb->mouse_pos.z = tb->radius * tb->radius -
                    tb->mouse_pos.x * tb->mouse_pos.x -
                    tb->mouse_pos.y * tb->mouse_pos.y;
  tb->mouse_pos.z = tb->mouse_pos.z < 0.0 ? 0.0 : sqrtf(tb->mouse_pos.z);

  n = sqrtf(tb->mouse_pos.x * tb->mouse_pos.x +
      tb->mouse_pos.y * tb->mouse_pos.y +
      tb->mouse_pos.z * tb->mouse_pos.z);

  tb->mouse_pos.x /= n;
  tb->mouse_pos.y /= n;
  tb->mouse_pos.z /= n;

  return;
}

void trackball_drag(struct trackball *tb, int nx, int ny) {
  float n;
  tb->mouse_old.x = tb->mouse_pos.x;
  tb->mouse_old.y = tb->mouse_pos.y;
  tb->mouse_old.z = tb->mouse_pos.z;

  trackball_proyect_mouse(tb, nx, ny);

  // Calculate rotation axis based on cross product
  tb->rot_axis.x = tb->mouse_old.y * tb->mouse_pos.z -
                   tb->mouse_pos.y * tb->mouse_old.z;
  tb->rot_axis.y = tb->mouse_old.z * tb->mouse_pos.x -
                   tb->mouse_pos.z * tb->mouse_old.x;
  tb->rot_axis.z = tb->mouse_old.x * tb->mouse_pos.y -
                   tb->mouse_pos.x * tb->mouse_old.y;

  // Normalize rotation axis
  n = sqrtf(tb->rot_axis.x * tb->rot_axis.x +
            tb->rot_axis.y * tb->rot_axis.y +
            tb->rot_axis.z * tb->rot_axis.z);

  tb->rot_axis.x /= n;
  tb->rot_axis.y /= n;
  tb->rot_axis.z /= n;

  // rotation angle
  tb->rot_angle = acos(tb->mouse_pos.x * tb->mouse_old.x +
                       tb->mouse_pos.y * tb->mouse_old.y +
                       tb->mouse_pos.z * tb->mouse_old.z);
}
